# Operations: Jafar interface, sessions, tokens

## Jafar interface (the whole surface)
1. Weekly brief (or per burst): one page: landed, in flight, blocked, numbers (throughput, budgets, judge agreement), next.
2. Decision queue: non-technical calls only, each a card: question, options, recommendation, consequence, deadline-if-any. Everything else is decided downstream and recorded.
3. Playtest requests: a build plus a 15-minute script of what to feel-check.
4. One-click runs: any local generation need ships as a .bat that is idempotent, non-interactive, logs to a file, writes outputs to a known folder, and prints DONE or the failure. Nothing that needs Jafar to babysit.
5. Status dashboard: dashboard.html and STATUS.md at the repo root, regenerated from repo state by tools/dashboard/build-dashboard.py (one click: open-dashboard.bat).

## The dashboard is DERIVED STATE (and so is every page like it)
1. The dashboard is a lens, never a source. If a number on it is wrong, the source file or the generator is wrong: fix one of those. Editing the page is editing a photograph of the problem.
2. The generator reads and writes nothing but its two artifacts. It never normalises, repairs or writes back to a source it read. Weekly process audit check 9 proves that rather than trusting it.
3. Chat is never a source of state. A number that exists only in a conversation is not state: it goes into the file that owns it, and the dashboard reads it from there or reports it as not yet applicable.
4. A panel with no source says so and names what it looked for. A zero on that page means a walk that examined something and found none; nothing-measured means the walk could not happen. The two must never render alike.

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

---

## Carried from CLAUDE.md (2026-09-01, task 013)

CLAUDE.md was cut to standing rules plus pointers because a 16,000-word file
read at the start of every session is a file nobody holds in their head. The
passages below are the operations half of it, moved intact: estimates,
promising to report back, not blocking yourself, the document rules, scope,
and the reporting shape. Original wording kept, per CLAUDE.md's own rule that
its older text is corrected opportunistically rather than rewritten wholesale.

Two pointers in the moved text are stale and are called out here rather than
edited into it, because the edit would hide what decayed. Under the Documents
rules, `roadmap.md` was the tiebreak under v1; the v2 plan is
ledger-v2/respec/roadmap-v2.md. The queue named there is game-design/queue.md,
which marked itself superseded on 2026-08-31; the live queue is
production/queue/ with production/NOW.md for what is already moving.

<!-- moved verbatim from CLAUDE.md lines 706-718 on 2026-09-01, task 013 -->

## 7. Estimates: name what dominates, or do not give a number

Wrong every time today. The causes were always the same two things:

- I benchmarked against a **broken** run (it was fast *because* it was
  cheating), and
- I did not check what was actually blocking — a run sat "pending" behind one
  of *my own* pushes three separate times.

**The rule.** Before giving an ETA, check the thing is actually running and
what is ahead of it in the queue. State what dominates the estimate (here: a
~28-minute CI round trip) and what could blow it up. If you do not know, say
so — that is a better answer than a number you will retract.

<!-- moved verbatim from CLAUDE.md lines 720-727 on 2026-09-01, task 013 -->

## 8. "I will come back to you" requires arming something

Said twice, and both times Jafar had to ask anyway. Ending a turn does not
schedule a wake-up.

**The rule.** If you say you will report back, start a background watcher in
the same turn that will fire on the condition (or a timeout). No watcher, no
promise.

<!-- moved verbatim from CLAUDE.md lines 729-737 on 2026-09-01, task 013 -->

## 9. Do not block yourself

Pushing a commit triggered a full 40-minute corpus fetch, three times, each one
queued in front of the run Jafar was waiting on. Once, the run that would have
*fixed* the problem was queued behind a run of the problem.

**The rule.** Know what your pushes trigger. Expensive jobs are opt-in
(`workflow_dispatch`), concurrency groups are scoped to the expensive job only,
and cheap checks never queue behind a stream.

<!-- moved verbatim from CLAUDE.md lines 739-756 on 2026-09-01, task 013 -->

## 10. Documents

Two failures, opposite directions, same day.

- The roadmap reached 1,525 lines of which ~85% was chronology, and I "audited"
  it by stamping a status banner on the top — certifying the mess.
- Then I over-corrected and split the plan into a second file, so you had to
  open two documents to find out what happens next.

**The rules.**
- Every doc in `game-design/` declares **LIVE / SPEC / LOG** in its first lines.
  `tools/docs-check.py` enforces it, plus: a LOG carries its date and says NOT
  CURRENT, a LIVE carries a verified date, a LIVE plan stays under 400 lines,
  and no LIVE doc contains a diary heading.
- **`roadmap.md` is the tiebreak and contains the plan itself.** Not a pointer
  to the plan. History goes to `roadmap-history.md`.
- A milestone entry is not a title. It states what is in it, why it sits there,
  **what done looks like as something measurable**, dependencies, and risk.

<!-- moved verbatim from CLAUDE.md lines 758-764 on 2026-09-01, task 013 -->

## A NEGATIVE CLAIM ABOUT THE REPO NEEDS A FETCH, A HEAD AND A COMMAND (L35, ruled 2026-09-02)

"X does not exist anywhere in this repository" is a claim about a whole
tree, and a local checkout is not that tree: it can be behind origin, and a
listing can be capped. Before writing one:

1. `git fetch origin <branch>`.
2. Search from HEAD OF THE WORKING BRANCH, not the working directory:
   `git ls-tree -r --name-only <sha>` or `git grep <pattern> <sha>`.
3. QUOTE THE COMMAND AND THE COMMIT HASH INSIDE THE CLAIM. A negative
   without its search is an opinion with a confident voice.

Never pipe a listing through `head` or `tail` and then describe the result
as the set. That is what produced this rule: `ls decision-register/ |
tail -6` returned six files, and "the register holds D4 to D9" went into a
decision record and a commit message. D10 had been there since `0ff1ee17`
and is cited from three documents.

The existing rule that every zero ships its denominator is the same rule
from the other end. This one names the case where the denominator is the
whole repository and the instrument is git.

## 11. Scope: do the asked thing

Asked whether a macOS build was *possible*, I built the CI job. Jafar:
*"never asked for a mac build, only if it's possible."*

**The rule.** A question is a question. Answer it, and offer the work
separately.

<!-- moved verbatim from CLAUDE.md lines 1512-1543 on 2026-09-01, task 013 -->

### Reporting — RETIRED 22 Aug by Jafar ("drop the updates")

No scheduled reports of any kind. Message him only when something needs
him, when he asks, or when a deliverable he waits on is ready. The style
lessons below survive for THOSE messages — they were learned expensively
and apply to any message he reads.

The retired schedule, for history: six times a day at 07:00, 10:00, 13:00,
16:00, 19:00 and 22:00 CEST.

**It opens with a header line so it can be FOUND**, then five to seven short
plain sentences:

    **LEDGER — 16:00** *(update 4 of 6)*

Then: what got done; where we are on the roadmap (read `roadmap.md`'s screen
table — do not recite from memory, and fix it if it is wrong before quoting it);
what is next; what decision is needed from Jafar, or "nothing needed from you".
Lead with anything visibly broken. **No code block, no template, no shas, no
metric names, no file paths.**

**The header exists because Jafar twice asked where an update was that had
already been sent.** Both times it was there and both times it read as more
conversation — I had followed the rule that it goes last with nothing after it,
which is right, and lost the signal anyway because nothing marked it. A report
he cannot find when scanning back is a report that did not happen, and the fix
is one line rather than more words.

He has said twice that updates were too long and too technical, and once that a
report was buried mid-message and he never saw it. Say *"the player is upside
down"*, not the name of the metric that measured it.

## HOW JAFAR IS TOLD THINGS, ruled by him 2026-09-02 after it went wrong

His words: "I just got back a wall of text with details I don't care about
... somewhere buried in that wall of text, it seems like you've asked me for
a decision ... and it's the only part that's relevant to me."

Three rules, and they are not style preferences.

1. **THE DASHBOARD IS THE UPDATE SURFACE, not the chat.** Progress, state and
   numbers go there and he reads them when he wants them. Regenerate and push
   the live document whenever something lands.

2. **ANYTHING NEEDING HIM GOES IN THE DECISION INBOX FIRST**, which is a
   `### ` heading under WAITING in `production/decision-queue.md` (retired
   2026-09-03: it was `game-design/decisions-pending.md`) and surfaces on the
   dashboard automatically. Written in PLAIN TERMS: what it means, the
   options with what each costs, and a recommendation, so it can be answered
   in one line. A decision mentioned only in chat prose does not exist; he
   has to be able to find it without reading everything else.

3. **CHAT IS SHORT.** It is for his questions and his answers, not for
   narration. No agent-by-agent accounts, no findings he did not ask for, no
   restating what the dashboard already says. If something genuinely needs
   his attention it is one or two lines pointing at the inbox entry.

WHAT THIS IS NOT. It is not permission to hide bad news or to stop recording
findings. Everything still gets written down in the repo, in full, with its
incident; that discipline is the project and it does not move. What changed
is WHERE it is written: the casebooks, the queue and the decision records,
not a message to Jafar.
