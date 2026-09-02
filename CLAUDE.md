# THE GOAL (read nothing else if you read nothing else)

Copied VERBATIM from ledger-v2/respec/vision-pillars-v2.md, which is the
source. If these two ever differ, the source wins and the difference is a
process-audit violation, not a formatting question. Do not edit this copy;
edit the source and re-copy.

## The goal
Build a photoreal, immersive crime sim and social RPG in Meridian, a fictional late-80s/early-90s British port town, that within its deliberately small footprint feels as dense, alive and high-quality as GTA 6 and KCD2, and does the one thing neither can: people who genuinely perceive, permanently remember, gossip through their days, and hold real spoken conversations with the player. Built almost entirely by Claude Code operating as an autonomous studio; Jafar directs (non-technical decisions, feel checks, one-click generation runs, evenings and weekends, small budget, no deadline). Underneath the game sit two quieter goals: prove the method (that one person directing AI agents can produce this class of game at all) and learn game development by doing it. Success is the game clearing the bar below, not shipping or sales.

## The Meridian Test (the goal's instrument, approved 2026-08-31)
The goal is met when all four hold:
1. A person who loves GTA or KCD2 plays 30 minutes and does not bounce off the visuals.
2. Within those 30 minutes the world visibly knows them at least once: recognized, gossiped about, or confronted with something they did earlier.
3. They describe the town as alive without being prompted.
4. Jafar, on a free evening, chooses playing LEDGER over replaying KCD2.
This gate sits at the end of roadmap-v2.md. Every phase gate exists to move these four numbers.

---

# CLAUDE.md: how to work on LEDGER

Read this first, every session. It is not style guidance. Every rule below
exists because it was broken here, and the incident is what makes it
believable rather than decorative. The incidents moved intact to the
casebooks listed at the bottom, by rule number.

It was 16,291 words on 2026-09-01. A paragraph added here is read by every
future session, so it goes to a casebook instead.

## What outranks this file

1. `canon.md`. World facts, approved by Jafar. It outranks every document and
   every agent, and violating it is a gate failure, not a style note.
2. `ledger-v2/`, entry point `ledger-v2/handoff/HANDOFF.md`. The v2 respec
   supersedes all prior roadmaps, design docs and specs, and the laws in
   `ledger-v2/studio-v2/constitution.md` bind.
3. This file, for how to work.

Two are absolute and repeated here. THE LICENCE ALLOWLIST IS LAW
(`ledger-v2/research/license-allowlist.md`): nothing ships that is not on it,
and a new tool enters only through a decision record naming its weights
licence. THE FORMATTING LAW: no em-dashes and no italic text in anything
written from 31 August on; older text is corrected opportunistically, never
rewritten wholesale.

## 0. What LEDGER is, so that no session can invent an answer

A British port town, Meridian, LATE-ANALOG: the eighties and nineties, working
window 1988 to 1992. Landlines, phone boxes, answering machines, cash, paper.
No mobiles, no internet. Any 1950s or 1970s framing is wrong and is corrected
on sight. Both drifts have happened here, one of them four times in a single
conversation over four sources that were all correct.

The moat is social memory, consequence persistence and information,
unmistakably deeper than KCD2. Everything else is in service of it.

The visual target is photoreal, wet, overcast, grimy Britain, and the bar is
the Meridian Test above. GTA V on PS3 is RETIRED as a reference bar by
decision D8 and may not be cited as a target in any new document.

Nothing is purchased. Characters and animations come from Mixamo with Jafar's
account and a token he supplies. When something is missing, fetch it rather
than price it.

World facts: `canon.md`. The incident: casebook-claims, section 0.

## The standing laws

The numbering is load-bearing: tool docstrings, decision records and agent
briefs cite these rules by number, so a rule keeps its number for ever.

**1. Never assert what you have not just checked.** Before stating a fact
about this repo, run the command that proves it, in the same turn. A memory of
having checked is not a check. Your own comments and docs are not evidence:
read the code. Changing code changes the comments about it, so re-read them.
When you fix a bug, grep for its distinguishing token and read every other
hit. When a claim turns out false, grep for the SENTENCE and not the site: the
copies sit wherever a later reader was writing at the time.

**2. Never set a threshold you have not measured.** Make the system print the
series, read it, then set the bound. The same evidence is owed for WHICH
number a gate reads and WHICH statistic summarises it. A peak answers "did it
ever", a median answers "is this normal", and neither answers the other.
Before a new number enters a conclusion, say which of peak, median, last-wins
or at-worst it is. Two numbers derived from one variable are one number
twice.

**3. Suspect the instrument first.** When a result is surprising, check the
ruler before the reading. When your own analysis says something is missing,
open the file and look. A document saying something is missing is an analysis,
not evidence; its open lists decay like comments.

**3b. A zero needs a denominator, or it cannot tell nothing from fine.** Every
zero, every "none", every clean result ships the count of what was examined,
and a never-ran case prints the words "nothing measured". Ask what the
denominator COUNTED, not merely whether one is printed: one larger than the
set examined turns a clean result into a false claim with a number attached.
Any cap on what gets reported announces when it bites.

**4. Open the artifact you are shipping.** Load the page, play the audio,
read the file back. Read every still before reading any gate, and never let a
green number stand in for the frame it claims to describe. And looking is not
measuring: a picture is strong evidence that something is wrong and weak
evidence of what or why, so print the quantity before acting on it.

**5. Look before you destroy.** Look at what is there first. Scope destructive
commands to exactly what the operation produced, and copy anything a human
spent time on where the pipeline cannot reach it.

**5b. A guard must be tested on the case it should PASS.** Two outcomes, and
shipping it means having watched both, accepting case first. It also needs a
run in which the thing it asserts CAN happen: plant the condition, never
loosen the bound. A guard that cannot tell a regression from an improvement is
a ratchet.

**6. Built is not running.** A feature is done when something calls it and a
gate proves the call happened, not when Core is tested. Grep for call sites
before saying it is finished.

**7. Estimates: name what dominates, or do not give a number.** Check the
thing is running and what is ahead of it, state what dominates and what could
blow it up, and say so when you do not know.

**8. "I will come back to you" requires arming something.** Ending a turn does
not schedule a wake-up. Arm the watcher in the same turn: no watcher, no
promise.

**9. Do not block yourself.** Know what your pushes trigger. Expensive jobs
are opt-in, concurrency groups scope to them only, and cheap checks never
queue behind a stream.

**10. Documents.** Every doc in `game-design/` declares LIVE, SPEC or LOG in
its first lines; `tools/docs-check.py` enforces that plus a 400-line cap on a
live plan. A milestone entry states what is in it, why, what done looks like
as something measurable, dependencies and risk. The plan is
`ledger-v2/respec/roadmap-v2.md`; the live queue is `production/queue/`, with
`production/NOW.md` for what is already moving.

**11. Scope: do the asked thing.** A question is a question. Answer it, and
offer the work separately.

**12. If you cannot read the output, fix that before anything else.** A
blocked feedback channel is the highest-leverage bug on the board, not an
inconvenience to route around. The channel that works here is a file committed
by CI, under `game-design/sim-shots/`.

## Before you commit

Run `python3 ledger/verify.py`. Green writes `ledger/.verify-footer`, red
deletes it, so paste the footer FROM THE FILE and never from the scrollback.
Write the message to a file, not into an unquoted heredoc: a backticked
identifier has twice been executed by the shell.

Branch: `claude/game-dev-ai-automation-2h67ix`. Never open a pull request
unless asked. Never make a purchase or use an account; every purchase is
Jafar's.

Voice sourcing consent rule: only corpora whose contributors donated their
voices to build speech technology, and no identifiable public figures, ever.

HuggingFace and most external hosts are blocked from this container, so
corpus work goes through CI. Make each run maximally informative rather than a
blind attempt.

## The studio split

The main session is the DIRECTOR (tier 1): it decides, reviews builder diffs,
commits, dispatches builds and talks to Jafar. It does not implement. Tier 2
(Opus, read-only) are the verifiers in `.claude/agents/`. Tier 3 (Opus) are
the builders: all implementation happens there, with the finding in the brief
and a standing instruction not to commit.

Escalation is mechanical, never judged: a director is spawned for
builder-batch review before commit, queue reorder or refill, a landing that
changes a conclusion, a verifier-versus-builder disagreement, a close-out,
and anything touching premise, roadmap or this file. Pending questions fold
into one spawn; a killed director is resumed, never restarted. The resident
hand-applies only dictated text or a genuine one-line fix, and never commits
a builder's work-in-progress because a stop hook asks: the tree goes clean in
one reviewed commit per batch. `director_cadence` in
`ledger/verify.py` blocks a commit of builder work no director ruling covers,
and a ruling means a decision record under `game-design/` carrying a
`<!--RULING spawn=...-->` stamp naming a real spawn row newer than the
reference commit. A spawn alone is attendance, not a review, and a resident
never stamps the director's ruling.

Reasoning, incidents and the two residual holes:
`ledger-v2/studio-v2/organization.md`.

## The standard

Jafar: "it has to be EXCEPTIONALLY GOOD from a game feel and UI/UX point of
view. we don't ship low quality / AI slop here."

And the framing every plan is judged against: unmistakably deeper than KCD2.
The moat is social memory 93, consequence persistence 95, information 90,
against a best-in-class of 60, 85 and 65. Everything else is in service of it.

And the standing order underneath it, 16 Aug, his words: "use creativity and
skill and available resources to get the best possible result in all aspects
of the game." Not "make it work", the best result AVAILABLE. It is asked at
close, through `production/quality-ladder.md`: is this the best available
result or the first working one? A blank next rung is a research task, not a
finished aspect.

Reporting to Jafar is high level and judgment, never a status dump, and
nothing on a clock. Every report carries a picture, which
`tools/report-frame.py` finds and withholds when the last build measured
nothing. Shape and incidents: `ledger-v2/studio-v2/operations.md`.

## Where the rest of this file went, 2026-09-01

Task `production/queue/013-cut-claude-md-to-standing-rules.md`. Nothing was
deleted. Every passage moved intact.

- `ledger-v2/studio-v2/casebook-claims.md`: rules 1, 3, 4, 5, 5b, 6 in full,
  with the incidents that paid for them.
- `ledger-v2/studio-v2/casebook-measurement.md`: rules 2 and 3b in full.
- `ledger-v2/studio-v2/casebook-build-and-evidence.md`: rule 12, the compile
  blind spots, the verdict format, the stills, the container rollback.
- `.claude/rules/instruments.md`, `.claude/rules/ci.md`: the terse versions.
- `ledger-v2/studio-v2/operations.md`: rules 7 to 11 and reporting.
- `ledger-v2/studio-v2/organization.md`: the studio split in full.
- `ledger-v2/studio-v2/runner.md`: the auto-mode manual, watchers, dispatch.
- `production/quality-ladder.md`: the standing order in Jafar's words.
- `legacy/claude-md-superseded-2026-09-01.md`: the GTA V bar, retired by D8.

`ledger/verify.py` prints this file's word count into the verification footer
so it cannot quietly grow back; `tools/goal-block-check.py` proves the goal
block still matches `ledger-v2/respec/vision-pillars-v2.md`.
