# Ruling: the return half and the correction. LAND WITH AMENDMENTS, ALL DICTATED

> **STATUS: LOG, 2026-09-08.** Director ruling on the uncommitted tree after
> `3cf7fc1`: 106 changed lines against the 100 threshold, workByScope
> tools:27/workflows:79, plus findings, budget and one brief with a sidecar.
> NOT CURRENT once the amended commit lands; from then the files are the
> reading copies and this is the record of why. Section 10 is a second look,
> resumed at 2026-09-08T02:46:56Z on the tree after `8921809f`.

VERDICT: LAND WITH AMENDMENTS. Every amendment is dictated text or a
one-line fix, so the resident applies it. Nothing here needs a builder.

- A1. The flush step has the same fault it claims to fix: its four status
  writes go to Jafar's checkout, not the runner's. Section 4. One line, twice.
- A2. The conclusion is half right. The return half stopped at 11:30 UTC on
  the 7th; the sending half did NOT "carry on": it was silent for the same
  fourteen hours and recovered at the 01:18 UTC restart. Section 1.
- A3. The brief overcorrects and omits the one consequence he needs.
  Replacement dictated and counted: 143 words of 150. Section 2.
- A4. `nothing failed to push: nothing was committed to push` is not what the
  evidence says. Dictated correction in findings. Section 1.

## 0. What this director could and could not check

This spawn had Read, Grep and Glob and no shell. So: no `git diff`, no
`git status`, no `git log`, no selftest run, no producer-check run. I read
the working-tree files and the CI-committed evidence directly. The 27/79
line counts and "107 checks" are the resident's numbers, unverified here.

What I did verify by reading:

- `production/pc-ops/push-diagnosis.txt` at 3cf7fc1: `lsRemoteSha` and
  `localTipRef` both `22973f8d...`, `onDisk_production_outbound=320`,
  `onDisk_production_inbox=2`, `pushDryRunExit=0`, receipts 27 to 30 with
  the times the finding quotes.
- The 11:30:08 UTC date of `22973f8d`, corroborated WITHOUT git:
  `scheduled-task-verify.txt` line 47 reads `pcInboxLastCommitAgeSec=51912`,
  taken by the step that runs just before the supervisor read at
  `@1788832519` (01:55:19 UTC). 1788832520 minus 51912 is 1788780608, which
  is 2026-09-07 11:30:08 UTC. Matches the claimed `13:30:08 +0200`.
- 312 files under `production/outbound/` in this tree (Glob count), against
  320 on his disk. Eight waiting, as the finding says.
- `production/inbox/` here holds README plus one message; his disk holds 2
  files. So no message of his is waiting, only outbound records.
- `production/d1-probe/ue-walk-verdict.txt` at `de4ad4d`:
  `launchStatus=LAUNCHED`, `piecesEmitted=593/593`,
  `walkCameraDistanceCm=618.2` MOVED, `collisionBlockedStatus=STOPPED` at
  `east_parade_bay0`, `testCardsSpawned=0/3`, `clipBytes=1642282`. The clip
  file exists. The brief's walk claims are covered.
- The sidecar is `...correction.brief.photo.txt`, which is what
  `sidecar_rel` (outbox.py:198) derives: it strips `.md` only. Correct name.
- `CAPTION_CAP=1024`; the brief goes out as one captioned clip, so its
  character count binds as well as its word count. Section 2 counts both.

## 1. Is the conclusion sound? Half of it.

THE QUESTION ASKED: does `localTipRef == lsRemoteSha` prove nothing FAILED
to push? No. Read `tools/runner/inbox.py:611-724`. The tip ref moves in
exactly one place, `update-ref` at line 710, and only after `ls-remote` at
701 has shown the remote holding the new commit. Every other exit from
`push_pending` (hash-object, update-index, write-tree, commit-tree, push
rc != 0, ls-remote mismatch) returns through `held()` and leaves the tip
where it was. So tip == remote is consistent with all of:

- `push_pending` never ran since 11:30;
- it ran and failed before building the commit;
- it built a commit and the push was refused or timed out;
- it pushed, and `ls-remote` did not show the commit.

The diagnosis step's own comment (workflow lines 236-238) states the
narrower, correct reading: a tip AHEAD of the remote would be "a push that
reported success and sent nothing". Agreement rules out that one shape and
nothing else. The finding's sentence "so nothing failed to push: nothing was
committed to push" is a hypothesis printed as a reading, and six lines later
the same finding admits "NOT YET EXPLAINED: why nothing is committed". It
should say "why nothing lands"; committed-or-not is precisely what is
unknown. The flush step is the instrument that answers it. Dictated text in
section 6.

THE SECOND CLAIM, WHICH NOBODY ASKED ME ABOUT AND WHICH IS WRONG: the
finding's title says THE SENDING HALF RAN ALL NIGHT, the flush step's header
says the sending half "carried on", and the new comment at
`telegram-bot.py:2372-2375` says "carries on perfectly". The same file
refutes it. The hypothesis-4 entry (findings.txt lines 336-341) records the
receipts as "two sends at 11:18 and two at 23:48, both being the bot's
startup pair ... with thirteen hours of nothing between", and the walk
answer, composed on the evening of the 7th, has `sent=01:35:46` on the 8th.
So from 11:30 UTC on the 7th to the 01:18 UTC restart on the 8th the bot
process was alive (supervisor: `telegram-botStarts=3 Stops=2`, both stops
the deliberate restarts) and did nothing in either direction. From 01:18 the
sending half works (ids 27, 28 at 01:18:47 are the startup pair; 29, 30 at
01:35:46 are the loop sending, seventeen minutes before the CI sweep at
01:52 could have) and the return half still does not.

WHAT THE EVIDENCE ESTABLISHES, stated so the brief and the finding can carry
it: the channel was not dead; it was silent for about fourteen hours with
the process alive, then half-recovered. "Dead since 11:30" was wrong about
the process throughout, and wrong about the effect only after 01:18. The
studio kept saying it after 01:18 because the half it reads through is the
half still broken. That last sentence is the lesson and it survives intact.

## 2. Is the correction honest? Not enough, in three ways.

The brief as written: "You were told your Telegram died at 11:30. That was
wrong; the studio's view of it died."

(a) It overcorrects. For fourteen hours the effect WAS a dead channel. The
honest word is silent, not "never dead". A correction that swings past the
truth is a second error he will have to be corrected on.

(b) "The studio's view of it died" is passive and actorless. The record
(five-rulings record line 38) shows he said "It died at 11:30" himself, off
the studio's report of a frozen counter, and the studio then repeated it
three times (findings.txt 310-311). The register bans "I was wrong" and
"correction:" (producer-check BANNED, self-correction), which is why the
writer reached for the passive. "The studio told you" is active and passes.

(c) It omits the consequence that touches him. The return half is STILL
broken. If he replies to this message, his reply is written to his disk and
may not reach the studio until the flush lands. "NEEDS YOU: nothing" is true
and insufficient: he has to be told that silence from the studio after his
reply is this fault and not his phone. "Your phone kept receiving" also says
continuity that did not exist.

REPLACEMENT, dictated in full in section 6. Counted by the rule
`count_words` applies (labels count, URL stripped, link text kept): 20 + 72
+ 3 + 18 + 28 + 2 = 143 of the brief cap of 150. Characters, which bind
because the message goes as a caption: about 850 of 1024. BUDGET is left
exactly as written because `SPLIT_PARTS` (producer-check.py:540) requires
the words studio, game, sessions, "not points" and "measured" in that
section, and "unmeasured" does not match `\bmeasured\b`. Ban list read
against the new text: no `key=value`, no run internals, no first-person
narration, no self-correction phrase, no bare digit count (clock times are
exempt). Link: one, to the map. NEXT VISIBLE THING carries "unknown".

CONDITION: my count is a hand count. Before commit the resident runs
`python3 tools/producer-check.py production/outbox/2026-09-08-the-street-and-the-correction.brief.md`
and pastes its `words:` line into the commit message. The register's number
decides, not mine. A refused brief is re-refused every 120 seconds for ever
(findings, 2026-09-07), so this is not optional.

## 3. Is the flush step worth 79 lines? The measurement yes, the lines no.

The step is the cheapest decisive measurement left. Four hypotheses have
been refuted by measurement; the only thing that separates "the flush never
runs" from "the flush runs and refuses" is running `push_pending` on his
machine with its output captured, which is what `--flush-inbox` does. It
sends nothing, loads no credentials, and if it works it restores the
studio's sight in the same run. The `pc-inbox` read step that follows it
already prints `pcInboxHeadShort` and age, so the run carries its own
effect check (rule 6, CI rule: effects not exit codes). Approved.

THE 79 LINES ARE THE STUDIO BUILDING ITSELF, and I say so plainly. About
fifty of them are a third copy of the python-finder and the
start/wait/kill/tail block that the sweep step already carries, and the copy
carried the sweep step's fault with it (section 4). This workflow now has
six steps that reach into his PC (install, diagnosis, sweep, flush, status,
pc-inbox read), each added on a day like this one, in a file that is 591
lines. Jafar narrowed the escalation rules on 2026-09-06 because of exactly
this pattern. The next window into his machine does not get written as a
fourth copy. Two queue items, named, not in this batch:

- QUEUE: fold the three run-a-tool-on-his-PC blocks into one script
  (`tools/runner/run-on-pc.ps1`: tool, args, out file, wait ceiling) so a
  window costs ten lines and a status-line fault cannot be copied again.
- QUEUE: retire the CI sweep step. Its question is answered
  (`alreadySent=7`, `sent=0`: the bot's own loop had already sent
  everything). What remains of it is a second sender racing the bot's
  120-second sweep on every push that touches this workflow, and one more
  refusal record per run for the 09-03 message. The comment's "receipts make
  a second send impossible" is true of sequential passes and not of two
  processes inside the same second. Named here; not blocking this batch,
  because this batch's push is the one that fires it and the brief goes to
  him by the bot's loop either way.

ONE MORE HAZARD, named and accepted: the CI flush and the bot's own
`flush_inbox` share `.git/ledger-inbox-index` and `refs/ledger-inbox/tip`.
If both run inside the same few seconds, one of them fails on the index and
says so. The output would then show a collision, not the underlying fault.
Read the flush output with that in mind; do not treat one odd failure line
as the answer.

## 4. The sweep step's missing status line: claim verified, cause wrong.

CLAIM VERIFIED: `outbox-sweep.txt` at 3cf7fc1 has `sweepPython=` on line 6
and `sweepStream=` on line 7, with no `sweepStatus` between them. True.

CAUSE, from reading the step (workflow 310-378) and not the file: `$out`
is the RELATIVE path `production/pc-ops/outbox-sweep.txt`. The header and
`sweepPython` are written before `Push-Location $repo` (353). BOTH status
lines (361, 365) are written between `Push-Location` and `Pop-Location`
(367). PowerShell resolves a relative path against its current location, so
those lines went to `C:\Users\Jafar\wc26-picks\production\pc-ops\outbox-sweep.txt`,
his checkout, which has that directory because the branch does. The stream
lines are written after `Pop-Location` (368-375) and so land in the
runner's file. The lines the file has are exactly the lines outside the
Push/Pop pair; `$raw` is absolute (`Join-Path $env:RUNNER_TEMP`), which is
why the python output was captured. The diagnosis step uses `-C $repo`
and never changes location, and it has every line. Rule 3: the finding
stopped at "the step left its own status branch without writing either",
which is an analysis; the file it should have opened was the step.

THE FLUSH STEP HAS THE SAME FAULT. `Push-Location $repo` at 415,
`Pop-Location` at 443, and all four `flushStatus=` writes (420, 428, 436,
440) sit between them. The comment at 422-426 claims the opposite. As
written, the first flush run would publish `flushPython=` then
`flushStream=` with no status, the "same-shape comparison" the finding
promises would come back with the same hole, and the write into his
checkout would dirty a tracked file there until pc-watcher's next hard
reset. This is the refusal in section 5 and it is fixed by one line each.

FIX IN THIS BATCH, not left: a one-line fix that makes an instrument tell
a hang from a clean exit is within what the resident hand-applies, and the
alternative is shipping a second instrument known to be blind on the exact
axis it was built to read.

## 5. What I refuse

1. The flush step as written (section 4). Passes with amendment W1.
2. The sentence "nothing failed to push: nothing was committed to push", the
   finding title "THE SENDING HALF RAN ALL NIGHT", the workflow header
   "while the sending half carried on", and the code comment "carries on
   perfectly". All contradicted by the batch's own hypothesis-4 entry.
   Amendments F1, W2, T1.
3. The brief's headline and first two sentences of WHAT CHANGED (section
   2). Amendment B1.
4. The second finding's cause paragraph. Amendment F2.
5. `flush done: pushed=0/0 nothing measured` on the path where the tool DID
   run and found zero waiting. "Nothing measured" is reserved for the
   never-ran case (rule 3b); a zero ships its denominator. Amendment T2.

Not refused, recorded: the `--flush-inbox` flag has no selftest row (grep
of the selftest for `flush-inbox` finds only the usage line and the branch
itself), so "107 checks" is consistent with the flag being unexercised. It
calls only tested functions and formats their dict; its first run is on his
PC. Acceptable for a diagnostic; the follow-up that folds the PC steps adds
a row. The two budget rows are approved as written: both say RECORDED LATE,
carry their dates, and the 9 the brief quotes is the governing Fable
reading at about 01:00Z.

## 6. The amendments, dictated

W1. `.github/workflows/ledger-install-supervisor-task.yml`. Line 317,
replace the whole line with:

    $out = Join-Path (Get-Location).Path "production/pc-ops/outbox-sweep.txt"

Line 387, replace the whole line with:

    $out = Join-Path (Get-Location).Path "production/pc-ops/inbox-flush.txt"

Both sit before their step's first `Push-Location`, so `Get-Location` is the
runner's workspace. The relative `New-Item` two lines below each stays.

W2. Same file, lines 396-398, replace the three comment strings with:

    "# half stopped at 2026-09-07 11:30 UTC. The sending half stopped too" | Add-Content $out
    "# and recovered at the 01:18 UTC restart on the 8th; this half did not," | Add-Content $out
    "# which is why the studio went on calling the channel dead after it sent." | Add-Content $out

Also lines 422-426: replace the comment's first clause "THE STATUS LINE IS
WRITTEN ON EVERY PATH, which the sweep step next to this one is not: its
own run published a python path and then jumped straight to the stream,
with no sweepStatus line on any branch of its if." with: "THE STATUS LINE
IS WRITTEN ON EVERY PATH, AND TO THE RUNNER'S FILE: $out is absolute
because both status writes here sit inside Push-Location, and the sweep
step's relative $out is how its status line landed in his checkout instead
(ruling 2026-09-08, section 4)."

T1. `tools/runner/telegram-bot.py` lines 2371-2375, replace the comment
with:

    # THE RETURN HALF, ON DEMAND. The bot pushes his messages and its own
    # receipts back to pc-inbox once a minute, and when that stops the
    # studio goes blind whether or not the sending half works. From
    # 2026-09-07 11:30 UTC both halves were silent; from the 01:18 UTC
    # restart on the 8th the sending half worked and this one still did
    # not, which is why the studio kept calling the channel dead after it
    # was sending. No credentials are loaded here. Nothing is sent.

T2. Same file, lines 2385-2386, replace the two-line `OUT.say(...)` with:

    OUT.say("flush done: pushed=0/0 waiting=0 tracked=%d, the branch already carries every file on this disk" % len(inbox.tracked_files(REPO)))

F1. `production/findings.txt`, first entry. Title lines 10-11 become:

    2026-09-08  THE CHANNEL WAS SILENT, NOT DEAD. BOTH HALVES STOPPED AT
                2026-09-07 11:30 UTC; THE SENDING HALF RECOVERED AT THE
                01:18 UTC RESTART ON THE 8TH AND THE RETURN HALF DID NOT.

Lines 13-16 become: "THIS CORRECTS A CLAIM MADE TO JAFAR. He was told his
Telegram channel had been dead since 11:30. The process was alive the
whole time (supervisor: Starts=3, Stops=2, both stops deliberate). From
11:30 UTC on the 7th to 01:18 UTC on the 8th it neither sent nor pushed,
which this file's hypothesis-4 entry below records from the receipts. After
the 01:18 restart four messages were accepted by Telegram while the studio
was still calling the channel dead: ids 27 and 28 at 01:18:47Z (the startup
pair), 29 (the map changed) and 30 (the walk) at 01:35:46Z."

Lines 25-29 become: "22973f8d is dated 2026-09-07 13:30:08 +0200, which is
11:30:08 UTC, corroborated from pcInboxLastCommitAgeSec=51912 in
scheduled-task-verify.txt without git. The local tip pointer and the remote
branch AGREE, which rules out one shape only: a push that reported success
and sent nothing. It does not say whether push_pending ran, built a commit,
or failed before, during or after the push; every one of those paths leaves
the tip where it is (inbox.py: each held() return, and the update-ref at
710 that runs only after ls-remote confirms). Eight outbound records sit on
that disk which the branch does not carry, and the eight newest receipts are
exactly the ones that would prove delivery. Ruled 2026-09-08."

Line 40, "NOT YET EXPLAINED: why nothing is committed." becomes "NOT YET
EXPLAINED: why nothing lands on the branch."

F2. Second entry, lines 51-55 become: "MEASURED: production/pc-ops/
outbox-sweep.txt at commit 3cf7fc1 carries sweepPython, then sweepStream,
with no sweepStatus key between them. CAUSE, found on director review
2026-09-08 by reading the step rather than the file: $out is a relative
path and both status writes sit between Push-Location $repo and
Pop-Location, so they landed in C:\Users\Jafar\wc26-picks\production\pc-ops\
outbox-sweep.txt, his checkout, not the runner's. The lines the file has
are exactly the lines outside that pair. The flush step beside it copied the
fault on all four of its status writes. Both fixed in the same batch by
making $out absolute before the first Push-Location."

Lines 60-62, the sentence beginning "The flush step added beside it today
writes its status on EVERY path" through "same-shape comparison." is
deleted; the paragraph ends at "was rewritten to make."

B1. `production/outbox/2026-09-08-the-street-and-the-correction.brief.md`,
whole file, verbatim, eleven lines with the blank lines as shown:

    HEADLINE: The studio told you Telegram died at 11:30. It went silent, not dead, and has sent again since 01:18.

    WHAT CHANGED: From 11:30 yesterday to 01:18 today it neither sent nor reported. A restart fixed sending: four messages since, the walk answer at 01:35. Still broken: nothing gets back to the studio, so your replies may sit unseen until that is fixed. The clip is the machine walking the street alone, the game's first moving picture: it launches, the street builds whole, a terrace wall stops it, open pavement does not.

    NEEDS YOU: nothing.

    NEXT VISIBLE THING: the crime, in that street, seen by one witness and overheard from another. When: unknown.

    BUDGET: nine percent on the governing meter when you read it this morning; unmeasured since. Studio versus game split: unmeasured; sessions, not points, until the rate is measured.

    [the map](https://jsab258.github.io/wc26-picks/map.html)

The sidecar is unchanged. "No test cards" is dropped on purpose: the walk
answer already told him that one is true by construction rather than
measured, and it bought three words.

## 7. Before commit

1. Apply W1, W2, T1, T2, F1, F2, B1 exactly. Nothing else changes.
2. `python3 tools/producer-check.py production/outbox/2026-09-08-the-street-and-the-correction.brief.md`
   prints SEND and a `words:` line under 150; paste the line.
3. `python3 tools/runner/telegram-bot.py --selftest` and
   `python3 tools/runner/outbox.py --selftest` (or however the outbox suite
   is invoked) still pass; paste the check counts.
4. `python3 ledger/verify.py` green; footer from the file.
5. Know what the push fires (rule 9): this commit touches the workflow, so
   the install workflow runs on his PC: install, diagnosis, sweep (SENDS the
   brief with the clip if pc-watcher has synced it first; otherwise the
   bot's loop does within two minutes), flush (pushes the eight records),
   status, pc-inbox read. Watch by ancestry for a landed run whose commit
   contains this one, then open `production/pc-ops/inbox-flush.txt` and
   read `flushStatus=` first. If that key is absent, W1 did not land.
6. The reading that closes this: `pcInboxHeadShort` in the same run's
   `scheduled-task-verify.txt` is no longer `22973f8`, OR `inbox-flush.txt`
   prints what `push_pending` refused and why. Either is an answer. A run
   with neither is NO RUN and says so.

## 8. Quality ladder at close

This is the first working rung for the return half, not the best available:
it restores sight once, on demand, and leaves the bot's own minute-by-minute
push unexplained. The next rung is whatever the flush output names. The
aspect whose next rung is blank is the instrument itself: the bot's stdout
reaches nobody, and every fault this week was one that printed its reason
to a window nobody reads. QUEUE: the supervisor already writes a status
file every 60 seconds; give each daemon's last twenty lines a place in it,
and let the status step that already exists carry them off the machine.
That is the window that makes the other six unnecessary.

## 9. Resident note, appended after the ruling, not part of it

B1 COULD NOT BE APPLIED AND IS DISCHARGED ANOTHER WAY. While this review was
running, the bot's own loop swept the outbox and sent the brief: it is
Telegram message id 31, sent 2026-09-08T02:34:14Z as a captioned animation
carrying production/d1-probe/ue-walk.gif, 907 characters, outbound latency
504 seconds. A sent message cannot be rewritten. Editing the file now would
leave the outbox holding text that never crossed, which is the one thing
this directory exists to prevent, so the brief stays exactly as it went.
Every other amendment (W1, W2, T1, T2, F1, F2) is applied.

THE RULING'S POINT STANDS AND IS ANSWERED BY A SECOND MESSAGE, written by the
Producer to say plainly that Jafar was right and the studio was wrong twice.
It carries the evidence this review did not have: the receipt reader was
widened from four to sixteen at commit 8921809, and it returned every receipt
on his disk, fourteen against a cap of sixteen, so the list is complete. It
reads id 24 at 2026-09-07T11:19:36Z, then NOTHING for twelve hours and
twenty-nine minutes, then ids 25 and 26 at 23:48:30Z, then the restart pair
at 01:18:47Z. Section 2's judgment was right and its numbers were generous:
the outage began at 11:19:36Z, not 11:30, and section 6's "from 11:30
yesterday to 01:18 today it neither sent nor reported" misses the two
messages at 23:48:30Z. Both differences are recorded here rather than edited
into the ruling above.

## 10. Second look, resumed at 2026-09-08T02:46:56Z, on the tree after 8921809f

Sections 0 to 8 are the ruling on the tree after 3cf7fc1 and are not edited.
This section is the review of what arrived after it: the applied amendments,
two additions, two facts, and one stamp. Same director, no shell, resumed
after a usage limit; the row is agent-log line 352.

WHAT THIS LOOK COULD READ, AND THE TREE CHANGED UNDER IT. Stated with the
instant each reading belongs to, from the evidence files, since I have no
clock of my own.

- The first read of this look, by grep, saw the amendments and both
  additions IN THE WORKING TREE: `Join-Path (Get-Location).Path` at
  workflow lines 304, 372 and 447; the W2 header at 456; `git add` of
  `inbox-flush.txt` at 624 and of `sends.tsv` at 628; in telegram-bot.py
  the case names `accept/flush-inbox-is-reached-from-main-and-returns-clean`
  (2308), `accept/flush-inbox-zero-carries-its-denominator-not-nothing-measured`
  (2311), `accept/flush-inbox-actually-calls-the-push-when-work-waits`
  (2329), `accept/flush-inbox-names-each-waiting-file` (2332), a fifth case
  around 2342 whose name the grep did not capture, `main(["telegram-bot.py",
  "--flush-inbox"])` called at 2306, 2327 and 2342, the zero case asserting
  `"nothing measured" not in zero_line` at 2313, the branch at 2433, T1's
  "both halves were silent" at 2437 and T2's `tracked=%d` at 2449.
- Every read after that saw none of it: telegram-bot.py at 2405 lines with
  no `--flush-inbox` branch, the workflow with no flush step, a relative
  `$out` at 328, no Q7, and no staging of inbox-flush.txt or sends.tsv.
  `.git/logs/refs/stash` says why: stash `cf31908c` at 1788835637, which is
  02:47:17Z, "flush+ledger: awaiting director re-stamp". A stash's objects
  cannot be read without a shell.
- The scratchpad copies I was pointed at (`workflow-with-flush.yml`,
  `telegram-bot-with-flush.py`) are the PRE-amendment batch, not the stash:
  the bot copy still carries "carries on perfectly" at 2373 and has no
  `tracked=%d` and no `accept/flush-inbox`; the workflow copy has the
  relative `$out` at 398, the old "carried on" header at 408, and no
  sends.tsv. They show neither the amendments nor the additions.
- In the working tree, read directly: F1 and F2 ARE applied in
  `production/findings.txt` and read correctly; F2 now ends "held with the
  step above", which is true. W1, W2, T1 and T2 are attested by the one
  grep above at the lines named, and by nothing else I could open.

So the spot-check is: F1, F2 read and correct; W1, W2, T1, T2 seen once by
grep in the pre-stash tree, at the right lines, with the right strings, and
not read in full. That is what it is, and it is written down as that.

RULING ON ADDITION 1, THE FIVE SELFTEST CASES. Approved, on a condition that
is evidence rather than trust. What the grep established: the cases call the
REAL branch (`main([... "--flush-inbox"])`, three times), and the zero case
asserts on the captured printed line, not on a stub's return (2313). That is
the honest shape. Stubbing `inbox.pending_all` and `inbox.push_pending`
tests the flag's control flow and formatting, which is everything the flag
contains; `push_pending` has its own suite in inbox.py with the autocrlf
accepting case. It would "test the stubs" only if a check read the stub's
dict instead of what `main` printed or returned. What I could not read: that
the stubs are set on the `inbox` module attributes the branch calls and
restored in a `finally`; that the zero case's stub raises; that the work
case asserts the call happened. CONDITIONS, both pasted into the commit
message: (1) the real selftest output with the five case lines and
`casesRun=112 casesFailed=0`; (2) a grep of every `check(` in that block
showing each one references `rc_zero`, `rc_work`, `rc_bad` or a captured
output line, and none references the stub's return dict. If either cannot be
produced, unstash and I read the bodies; that costs one turn and no seat.

RULING ON ADDITION 2, `production/pc-ops/sends.tsv`. REFUSED for this batch,
on four grounds that do not depend on the block's body, which I did not
read. Pull it out of the stash before the commit.

(a) The instrument already exists. A receipt file
`production/outbound/<stem>.receipt.txt` carries `messageId:`, `sent:` and
`file:`, is written only after Telegram accepted, and reaches the working
branch through pc-inbox and `tools/inbox-read.py`: this tree holds eight of
them today (ids 13, 16, 17, 18, 19, 22, 23, 24), which is how the diagnosis
step could print them. Id 31's proof "lives one run" only because the return
half is broken, and the return half is the fault under diagnosis. A second
transport for receipts because the first is down is the pattern this
workflow's own header (lines 124-133) refuses in its own words.
(b) The ruled pattern for durable CI evidence is in `.claude/rules/ci.md`
already: per-run copies keyed by short sha. If the pc-ops files must survive
the next run, copy them under `production/pc-ops/runs/<sha>/` in the commit
step, staged by name. Three lines, no new format. Queue item, not this batch.
(c) A tally, a dedup and a formatter written in pwsh inside a workflow step
is the untested top-layer formatter `.claude/rules/instruments.md` forbids
("put the tally, the maths and the string in the tested layer"). If a ledger
is ever wanted, `inbox-read.py` already parses receipts in Python under a
selftest and is where it belongs.
(d) It is a seventh window into his PC, on the day the fourth, fifth and
sixth were added. Section 3 said the next one is not written as a copy.

On the sub-questions, recorded for whoever takes the queue item: the receipts
are the right source and the sweep's stdout is not, precisely because
receipts capture the bot's own loop; dedup by Telegram message id is safe
against a rewritten receipt (same id, same row) and correct for a resend
(new id, new row), provided rows with `messageId=none` are skipped and
counted; a run that can read nothing writes NOTHING to the ledger and prints
`sendsLedger=nothing-measured receiptsExamined=0 reason=...` in the
diagnosis file, which staging without `-A` already half-does. The ladder's
done token for the street step is `messageId: 31` in the brief's receipt
file once the return half lands it, not a new column.

TWO CORRECTIONS TO SECTION 9, AND ONE TO MY OWN NUMBERS.

(1) Section 9 says the bot's own loop sent the brief. The file it cites says
otherwise. `outbox-sweep.txt` at 8921809, line 9, is the CI SWEEP STEP's own
stdout: `04:34:14 outbox: sent ...brief.md kind=brief AS-CAPTIONED-CLIP ...
messageId=31`, with the done line `captionedClipsSent=1`. The sequence:
8921809f pushed at 02:33:47Z touching the workflow, which fires it;
diagnosis at 02:34:07Z; sweep at 02:34:10Z; message 31 at 02:34:14Z. The
push that carried this ruling into the repository fired the sender that sent
the text the ruling refused, fifteen minutes after section 3 named that
hazard and declined to block on it. The bot's loop had no chance: the brief
reached his checkout with that push. And `outboundLatencySec=504` is
commit-to-send; roughly eight of those minutes are the brief sitting
committed and unpushed in the container, so that number describes the
container's push cadence, not the transport.

(2) Therefore the CI sweep step is retired IN THIS COMMIT, not queued as
section 3 had it: the stashed batch touches the workflow, and the push will
fire the step again with the second correction sitting in the outbox.
One-line fix, dictated: in the step named "Run one outbox sweep on his
machine and print what it says", replace `if: always()` with `if: false`
and change nothing else. `outbox-sweep.txt` stays in the tree naming
8921809 on line 1, which is what line 1 is for. This is not adjacent work:
the step is in the batch and it just produced the outcome the batch exists
to correct.

(3) My section 6 sentence "from 11:30 yesterday to 01:18 today it neither
sent nor reported" is wrong twice by the widened reader, which returned
fourteen of a cap of sixteen and is therefore the whole list: the gap opens
at 11:19:36Z (id 24), not 11:30, and ids 25 and 26 at 23:48:30Z, the 23:48
restart's startup pair, sit inside it. Section 2's judgment stands and its
numbers move: twelve hours twenty-nine minutes of nothing, two startup
notices, ninety minutes of nothing, then the restart onto the poll fix. The
return half's 11:30:08Z is a different clock (the last push), and the two
are not to be conflated again.

RULING ON THE SECOND MESSAGE,
`production/outbox/2026-09-08-you-were-right-about-11-30.unprompted.md`. It
does two of the three things B1 was for: the actor is named ("the studio's
last message was wrong") and the standing consequence is stated ("any reply
may sit unseen"). It fails the third on one sentence: "The fix awaits
review." No fix exists in the tree or the stash; the flush step is a
measurement, and the cause is unknown. That sentence is the class of claim
this whole day has been correcting. Two smaller faults: "normal since a
restart at 01:18" rests on one pair at 01:35, since id 31 went through CI
and not the loop; and "You were right" overshoots his sentence, which was
right about the effect and unproven about the cause (the supervisor's
counters show no stop at 11:30). Dictated as B2, whole file. Counted by
`count_words`: 25 + 52 + 3 + 18 + 15 = 113 of the unprompted cap of 120.
The split sentence is dropped: `split` is enforced in the brief register only
(`RULES_BRIEF_ONLY`), and he received it in message 31 at the same reading.

B2, verbatim, nine lines with the blank lines as shown:

    HEADLINE: You were right that it stopped, and the studio's last message was wrong: your Telegram sent nothing for twelve and a half hours yesterday.

    WHAT CHANGED: Second correction tonight; the receipts on your PC settle it. Nothing sent between about 11:20 and 23:48 UTC; sending again since a restart at 01:18. Still broken: nothing from your PC has reached the studio since 11:30 yesterday, so any reply may sit unseen. The cause is not yet known.

    NEEDS YOU: nothing.

    NEXT VISIBLE THING: the crime, in [that street](https://jsab258.github.io/wc26-picks/map.html), seen by one witness and overheard from another. When: unknown.

    BUDGET: nine percent on the governing meter when you read it this morning; unmeasured since.

Ban list read against it: no `key=value`, no run internals, no first-person
narration, no "correction:" with a colon, no bare digit count (four clock
times, exempt). One link, to the map. "unknown" present. NEEDS YOU parses
as zero items. CONDITION: the resident runs producer-check on it and pastes
the `words:` line. And it goes to him by the bot's loop only, which is why
(2) above lands in the same commit.

THE STAMP, one paragraph because the next person to write one will read
this. This record closes with a stamp naming 2026-09-08T02:46:56Z, the row
this resume created (agent-log line 352), which is newer than the
reference `8921809f@02:33:47Z`. My original row, 02:21:36Z (line 349), is
older than that commit and would read as a ruling on the batch before it,
which is the gate being right. The bare form `spawn=studio-director` that
this record carried at first did not pair at all, and the failure is the
quiet kind: the gate counts a stamp it cannot match to a row under
`rulingUnmatched` and then DROPS it, so it reads exactly like no ruling,
silently, instead of refusing loudly. A stamp names a row from
`.claude/agent-log.tsv`, verbatim, or it is invisible. That the gate drops
rather than refuses is a rule-3b hole worth a queue line of its own: an
unmatched stamp is a zero that lost its denominator. The record carries the
comment form exactly once, on its last line, because `RULING_RE`
(verify.py:2870) matches it anywhere in the file.

LINE COUNT. This record passes 400 lines with this section. docs-check's
cap binds LIVE plans only (`tools/docs-check.py:162` skips every other
banner); this is a LOG and stays whole rather than losing its history.

BEFORE THIS COMMIT, in addition to section 7: unstash `cf31908c`; remove
the sends.tsv block and its `git add`; apply the `if: false` in (2); apply
B2; paste the three things named (selftest output with the five case lines,
the `check(` grep, producer-check's `words:` line for B2); then verify.

<!--RULING spawn=2026-09-08T02:46:56Z-->
