# Ruling: Director's Console step 2, the governance batch

> **STATUS — LOG, 2026-09-03.** Director ruling, reference commit adf24305.
> NOT CURRENT once its five fixes are applied and the batch is committed;
> from then the committed files and `production/decision-queue.md` are the
> reading copies and this is their history.
Reviewed by reading; see "What this ruling did not measure" before treating
any statement here as a measurement.

VERDICT: LAND, WITH FIVE FIXES FIRST, and one named item that must land before
the second Producer message is ever sent. The batch matches what Jafar ruled on
every design point. The faults are in the seams: an instruction the Producer
role cannot physically execute, a link floor that depends on a word list, an
artifact that still names the retired file, and an approved addition with no
carrier.

The design is not re-opened. Jafar ruled every point in writing on 2026-09-03
and this ruling checks the build against his words, nothing else.

---

## 0. What this ruling did not measure

No command was run in this session. This director has Read, Glob, Grep, Write
and WebSearch, and no shell. Every statement below is read off the files in the
tree at the time of review. In particular:

- `python3 tools/producer-check.py --selftest` HAS NOT BEEN RUN IN ANY SESSION
  THIS RULING CAN SEE. The builder reports it ran and found two bugs in itself.
  That is prose, not evidence, and rule 1 says a memory of a check is not a
  check.
- `python3 tools/blocking-count.py --selftest` likewise.
- The exit codes, the counts and the report lines quoted below are read off the
  source, not off a run.

This is FIX 1 and it is the cheapest decisive measurement in the batch.

---

## A. The check's definition of a claim

RULING: the definition is STRUCTURALLY SOUND and its RECALL IS NOT. It is safe
to land, and it may not be left as the load-bearing half of constitution law
12.

What is right, and it is not a small thing. The definition is three named
conditions, it is printed in the report verbatim (`producer-check.py` line 551)
so a finding can be audited without reading the function, and both bugs the
builder found are real fixes that are present in the code:

- the section label is stripped from the line before the prefix test
  (`sentences()`, the `body = line.split(":", 1)[1]` branch), so HEADLINE's
  sentence is a claim again;
- `find_counts()` blanks every path before counting numerals, so
  `production/queue/062-uv.md` is one violation and not two.

The second fix is PINNED by a test that can go red: the selftest asserts every
rejecting fixture trips exactly one rule, so a returning double-report turns
`banned:file path` into two rules and fails. The first is pinned only by
`r["claims"] >= 2`. Reading the fixture by hand, the fixed code finds 2 claims
in GOOD and the buggy code finds 1, so the assertion does catch that exact
regression, by one. That is a margin, not a test. Ask for the direct assertion:
the HEADLINE sentence is claim-shaped.

WHICH DIRECTION THE ERRORS FALL. Both directions, on different rules, and the
pairing is backwards.

1. CLAIM DETECTION UNDER-FLAGS, systematically. `ASSERTION_RE` is a closed list
   of about thirty verbs: the copulas, the auxiliaries, and a set of
   project-flavoured participles (landed, shipped, wired, rendered). Ordinary
   English assertion outside that list is invisible. "The street looks right."
   "Textures now cover the whole town." "Nothing needs you today." "The crowd
   packs to touching distance." "Two weeks remain." None of those is
   claim-shaped to this check.

   THE EVIDENCE IS IN THE BUILDER'S OWN ACCEPTING FIXTURE. `GOOD` contains at
   least five sentences a person would call claims and the check finds two.
   "the grey street now paints properly" (paints), "Everything else waited on
   that" (waited), "£0 spent, well inside the month" (spent) are all missed.
   A 40 percent recall on the only compliant message the project has is not an
   edge case; it is the normal case.

2. THE BAN LIST OVER-FLAGS, on this project's own vocabulary. `run internals`
   matches `gate|gates`, `job|jobs`, `branch\w*`, `commit\w*`, `dispatch\w*`
   case-insensitively. Meridian is a port town with dock gates, and the game is
   about jobs. `commit\w*` matches "commitment". `find_counts` scrubs ISO
   dates, clock times, named-month dates, money, durations, list labels and
   product names, and a bare year does not survive any of them: "the town reads
   as 1989" is reported as a count, in a project whose working window is 1988
   to 1992.

WHY THE PAIRING IS THE PROBLEM. The rule Jafar made law is the link. The link
floor fires only when `claims and not good_links` (line 391). So the one rule
that carries constitution law 12 is the permissive one, and the merely
stylistic rules are the aggressive ones. That is precisely the arrangement that
trains a user to overrule the tool while the law goes unenforced: the check
cries wolf about the word "gate" and stays silent on a message with no evidence
in it at all.

THE FIX IS SMALL AND IT REMOVES THE VERB LIST FROM THE LOAD-BEARING PATH. In
the unprompted and brief registers, at least one qualifying link is REQUIRED
unconditionally. Those registers mandate WHAT CHANGED; a message with nothing
to link to is not a message. Claim detection then keeps the job it is actually
good at, which is producing the per-section series the advisory already prints
with its denominator, off which a stricter per-claim bound gets read later.
That is rule 2 followed properly: ship the printer, read real messages, then
set the bound.

One smaller hole, worth naming rather than fixing now: `NON_CLAIM_PREFIX`
exempts the whole LINE, so any sentence sharing a line with an option,
recommendation, default or deadline marker is exempt. A writer avoiding the
link floor has a one-character route to it.

---

## B. The enforcement point

RULING: the builder's REASON is accepted and its CONCLUSION is not, and there
is a harder fault underneath both that neither the brief nor the builder named.

The reason is right. This repo registers SessionStart, PreToolUse and
SubagentStart and no Stop or SubagentStop hook. A SubagentStop hook fires for
every agent in the studio while only a fraction of any agent's output is a
Producer message, and a check that fires on the wrong population produces false
alarms. False alarms teach people to overrule the tool. That reasoning stands
and is recorded.

The conclusion does not follow. "No SubagentStop hook" and "no mechanical
enforcement anywhere" are different findings, and the builder took the second
from the first. Jafar's brief said MECHANICALLY CHECKED BEFORE SENDING, and his
approved order names item 3 as "the register plus its Stop-hook check" at 3
points. A check run by hand is a mechanical check with a manual invocation,
which is rule 6 wearing a lab coat: grep finds `producer-check.py` named in
`.claude/agents/producer.md` and `.claude/agents/README.md` and nowhere else.
No call site in `ledger/verify.py`, none in `.github/`, none in a hook.

THE HARDER FAULT. `.claude/agents/producer.md` frontmatter is
`tools: Read, Glob, Grep, Write` with `disallowedTools: Bash`. Lines 83 to 87
of that same file instruct the Producer to run
`python3 tools/producer-check.py <file>`. THE PRODUCER CANNOT RUN THE CHECK
THAT ENFORCES ITS OWN REGISTER. The one instruction that makes the register
binding is impossible for the role it is written for.

AND THAT CREATES A DEADLOCK THIS BATCH WOULD HAVE COMMITTED. CLAUDE.md line 170
now says the director "does not address Jafar", and line 205 says reporting is
the Producer's alone. The moment that lands, the only role permitted to speak
to Jafar is a role whose mandatory pre-send check it cannot execute. Nobody can
talk to him without breaking a written rule.

THE RESOLUTION, and it is cheap. The Producer WRITES the message to a file; the
SENDER runs the check and reads what it printed. That is a real enforcement
point with the right population and no false-alarm surface, it exists today,
and it dissolves the deadlock in one dictated paragraph. It is FIX 2 and it
blocks the commit, because the alternative is committing an instruction that
cannot be followed.

The mechanical half then lands as the named item below, at the one trigger
whose population is exactly right: a message directory, and a verify check that
every file in it exits 0. Not every agent's output. Not a hook. The files that
are, by definition, Producer messages.

---

## C. The dashboard reading a file nothing writes

RULING: the repoint discharges the instance. IT DOES NOT DISCHARGE THE FAULT,
and the fault gets its own queue item. This is the most valuable thing in the
batch and the builder was right to surface it above the item.

The finding, restated so it cannot shrink back into a detail: the console's
needs-you count read `game-design/decisions-pending.md`, a file the project had
stopped writing to. It was correct on 2026-09-03 only because the retired file
still carries the same card as history. It would have gone wrong silently the
first time a card was added or struck, and it would have gone wrong CONFIDENTLY:
a number with a stated derivation, on the panel that exists to get decisions out
of Jafar.

The existing machinery cannot see this class. `SOURCES` in
`build-dashboard.py` exists so that a MOVED file shows as an absent source
rather than a silent zero, and `Reading.unavailable` handles the missing case.
Neither sees a source that still exists and has simply stopped being written.
Absence is handled; STALENESS is not. And constitution law 8 already says a
stale document is a failing test, which makes this an unenforced law rather
than a new idea.

THE INSTANCE IS NOT EVEN FULLY CLOSED IN THIS BATCH. `STATUS.md` line 18, the
artifact the console actually ships, still reads:

    ('### ' headings in game-design/decisions-pending.md, ... of 10 heading
    line(s) read in 1 file, of which 1 are cards)

generated at 11:44. The source was repointed and the artifact was not
regenerated, so the batch as it stands ships a console that contradicts its own
source table. Rule 4: open the artifact you are shipping. That is FIX 4.

Two more live pointers at the retired file, both of which will send a future
session or builder at it:

- `ledger-v2/studio-v2/operations.md` line 203, the process rule for "anything
  needing him", still names `game-design/decisions-pending.md` as the inbox.
- `production/queue/049-...md` lines 3 and 12, a READY card whose acceptance
  says the dashboard renders "from decisions-pending.md rather than retyped".

That is FIX 5, and it is the reason the class needs an item: one repoint left
three readers pointing at a dead file, and only the one somebody happened to be
editing got fixed. Grep for the sentence, not the site.

QUEUED, not done here: every entry in `SOURCES` prints how long it has been
since its source last changed, beside the reading it produced, with the words
nothing-measured when it cannot tell. Printer first, no threshold, per rule 2.

---

## D. The answer register's exemption

RULING: printing the unenforced rules is the right remedy and is correctly
applied. Two amendments, one of which is required.

What is right. `report()` prints "NOT ENFORCED in this register, named rather
than skipped in silence: wordcap, shape, options, deadline, nextvisible", and
the clean line carries its denominator: "0 finding(s) over 2 rule(s) enforced
(banned,linkfloor)". That is rule 3b satisfied at the point it matters, and it
is the exact remedy this project settled on for a check that would otherwise
pass by not looking. `COUNTS_ALLOWED_IN` is a named set at module level, which
is the greppable constant Jafar required.

AMENDMENT 1, required. The verdict line is `producer-check: SEND` and it says
nothing about how much was enforced. A 2-of-7 pass and a 7-of-7 pass exit 0 and
end with the same sentence. The last line is the one a human reads and the one
the Telegram bot will grep, so it is the line that must carry the number:

    producer-check: SEND register=answer rulesEnforced=2/7

Whole-run numbers on the done line. It is the project's own instrument rule and
it costs one format string.

AMENDMENT 2, required, and it protects Jafar's ruling rather than extending it.
The answer register drops `options` and `deadline`. So an answer that also asks
him to rule something escapes the two-to-four options, the recommendation, the
default and the 24 hour floor entirely. He ruled that length follows the
question. He did not rule that a decision buried in an answer needs no default.
Enforce `options` and `deadline` in the answer register WHEN A NEEDS YOU
SECTION IS PRESENT. It cannot fire on a message without that section, so it
adds no false-alarm surface.

---

## E. What does not match what Jafar ruled

Point by point against his words. Four match cleanly, two do not.

MATCHES.

- CLAUDE.md line 169 to 170 reassigns the channel, and line 205 to 210 follows
  through: "Reporting to Jafar is THE PRODUCER'S ALONE, ruled 2026-09-03.
  Resident owns the record, Producer the channel." Both halves changed, not
  one.
- Constitution law 12 carries both halves of his resolution: evidence layers by
  audience, the link is REQUIRED rather than optional, and "a claim with no
  artifact behind it may not be sent". It names the contradiction it resolves.
- n8n is struck from `runner.md`. The word survives exactly once, in the
  sentence that strikes it, which is the correct form: the strike is a record,
  not a leftover option.
- The one decision flow is built as ruled. One file holds WAITING and RULED,
  the dashboard reads WAITING for needs-you and BOTH halves of the register for
  decided with both denominators printed, the legacy card is migrated with its
  options, recommendation, default and deadline intact, and the legacy file
  carries its retirement banner. `read_decisions` also reports any section that
  is neither WAITING nor RULED rather than re-bucketing it.

DOES NOT MATCH, 1: AN APPROVED ADDITION WITH NO CARRIER. Jafar approved three
additions: the evidence floor, A LIVENESS ROW ON THE CONSOLE, and the Blocking
counter before its threshold. Two landed. The word "liveness" appears nowhere in
`production/`, nowhere in the queue, and nowhere in the dashboard; it exists
only in the step 1 brief that proposed it. Its absence from THIS batch is
correct, because his ruled order for the week is items 6, 1, 3, 4 and the
amendment, and the console items are not in it. Its absence from the QUEUE is
the drift: an approved item with no card is an approval that decays into a
preference by Monday. It needs a card, today, with the reason it is deferred.

DOES NOT MATCH, 2: THE ENFORCEMENT POINT, ruled at B above. His brief said
mechanically checked before sending and his approved order names item 3 as "the
register plus its Stop-hook check". What shipped is a check run by hand, in a
role that cannot run it. The builder's objection to the specific mechanism is
sound and is upheld; the reduction of the ruled item is not, and it is restored
at a different trigger rather than sent back to him, because the fix is small
and his intent is not in doubt.

NOTHING ELSE DRIFTED. The resident applied his words accurately.

---

## The first ruled card: CONFIRMED CORRECT

Checked against the file, not against the claim.

- Option A, the Unreal wire, one session. `production/decision-queue.md` under
  RULED THIS WEEK: "RULED BY JAFAR. Option A. One session."
- Carried into queue 062. The card names
  `production/queue/062-uv-chain-head-refuses-to-wire.md`, that file exists, it
  carries `max_sessions: 1` matching "one session", and it is the live blocker
  under the stop rule.
- Recorded as a lighter RULING and not a D-record, on the stated ground that it
  schedules work rather than changing architecture or identity. That is the
  correct side of the line Jafar drew, and the dashboard counts it in the
  decided half with the D-record count printed separately, so choosing the
  lighter form does not hide it.
- It is the week's first ruled card and it is the only one.

---

## The fixes, in order

BEFORE THE COMMIT. All cheap: two commands, one regeneration, three dictated
edits.

1. RUN BOTH SELFTESTS and paste the two result lines into this record.
   `python3 tools/producer-check.py --selftest` and
   `python3 tools/blocking-count.py --selftest`. If either is red, everything
   above is provisional. Nothing in this batch has been executed anywhere this
   ruling can see.
2. `.claude/agents/producer.md`: the Producer WRITES the message file; the
   SENDER runs the check and reads what it printed. Remove the instruction the
   role cannot execute. This is the deadlock fix, not a wording preference.
3. `production/queue/`: a card for the liveness row, marked deferred behind the
   console items, so the approval has a carrier.
4. Regenerate `STATUS.md` and `dashboard.html`, then OPEN `STATUS.md` and
   confirm the decision inbox derivation names `production/decision-queue.md`
   and carries the CLASS breakdown. Do not read the exit code for this.
5. Repoint `ledger-v2/studio-v2/operations.md` line 203 and
   `production/queue/049-...md` lines 3 and 12 at
   `production/decision-queue.md`.
6. `production/NOW.md`: the Producer channel rule in the standing hazards,
   today's budget number, and the ruled card. It is the file a fresh session
   opens first and it currently describes a studio in which the resident still
   talks to Jafar.

THE NAMED ITEM, one builder pass, and NO SECOND PRODUCER MESSAGE GOES TO JAFAR
BEFORE IT LANDS.

- The link floor becomes unconditional in the unprompted and brief registers.
- The verdict line carries `register=` and `rulesEnforced=N/7`.
- `options` and `deadline` are enforced in the answer register when a NEEDS YOU
  section is present.
- Both selftests are wired into `ledger/verify.py`, so neither instrument can
  decay quietly. Neither is called by anything today.
- A named message directory, and a verify check that every file in it exits 0
  on `producer-check.py`. That is the population-correct enforcement point.
- Delete the two dead assignments to `linked_sections` in `producer-check.py`
  before the third one, and pin the HEADLINE regression directly rather than
  through a margin of one.
- `blocking-count.py` selftest, the space-in-value assertion: `done.split()`
  cannot yield a token containing a space, so `all(" " not in tok ...)` is
  vacuously true. A check that passes by not looking, inside the instrument
  written to stop that. Assert over the unsplit string.

QUEUED SEPARATELY, not this week: a source-staleness reading on every dashboard
`SOURCES` entry, printing days since last change beside each reading, with the
words nothing-measured when it cannot tell. Printer first, bound later.

---

## The quality ladder at close

Not the best available result, and the next rung is known rather than blank, so
this is not a research task.

The register instrument's rung is lexical. It matches verbs from a list and
tokens from a list, which is why it misses "the street looks right" and flags
the dock gates. The next rung is not a better word list; it is to stop the
load-bearing rule from depending on word lists at all, which is the
unconditional link floor above. The rung after that, when real messages exist,
is the per-claim linkage bound read off the series the advisory already prints.

The governance rung is that this batch changes who may speak to Jafar and the
new speaker's compliance is verified by a human remembering to type a command.
The next rung is the message directory and the verify check. It is named, it is
small, and it is in the item above.

---

<!--RULING spawn=2026-09-03T12:26:38Z paths=.claude/agents/producer.md,tools/producer-check.py,tools/blocking-count.py,production/interrupt-classes.md,production/interrupt-log.tsv,production/decision-queue.md,tools/dashboard/build-dashboard.py,CLAUDE.md,ledger-v2/studio-v2/constitution.md,ledger-v2/studio-v2/runner.md,game-design/decisions-pending.md,production/queue/062-uv-chain-head-refuses-to-wire.md,STATUS.md,game-design/decision-2026-09-03-directors-console-step-2.md-->
