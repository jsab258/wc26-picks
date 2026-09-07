# Ruling: the remote restart job, and the pair of processes it would have refused. AMEND, THEN LAND IN TWO COMMITS

> **STATUS: LOG, 2026-09-07. NOT CURRENT** once the amended batch lands in
> the two commits section 8 orders and the restart evidence file exists on
> the branch. Director ruling at spawn 2026-09-07T22:52:34Z
> (`.claude/agent-log.tsv` line 345) on the uncommitted tree after
> `a766deca` (22:25:53Z): 462 changed lines against the 100 threshold, three
> new files and three edited, 0 director rows newer than the reference. The
> row between the last ruling and this spawn is line 344,
> `2026-09-07T22:37:44Z general-purpose`. This is the ruling the 21:57:03Z
> record's section 5 item 3b and section 7b said route b would need; that
> record dictated the behaviour and did not cover this diff. NOT CURRENT
> once the amended commits land; from then the files are the reading copies
> and this is the record of why.

VERDICT: AMEND, THEN LAND IN TWO COMMITS. The diff implements section 5 item
3b as written. It is not safe to point at his PC as written, because item 3b
was written about a machine with one bot process and the evidence that landed
after that ruling shows the machine runs every daemon as two. Four block, four
ride the same pass, and this record amends its predecessor's own count.

- B1. The match finds TWO processes for one bot on his machine and refuses
  on the accepting case; naively fixed, it would kill the wrong one of the
  two and leave the live bot running beside its replacement. Section 1.
- B2. The 5 second wait is a bound set without a series; on the expected
  path it prints `stopped-but-did-not-come-back` about a bot that came back
  one second later. Section 2 and 5.
- B3. This landing fires BOTH workflows on one push, both rewrite
  `production/pc-ops/supervisor-status.txt`, and the second one's rebase
  conflicts on its first line, so the destructive job's evidence dies on the
  agent if it runs second. Section 3.
- B4. The restart step buffers the script's output until the child exits;
  a timeout after `Stop-Process` leaves no record that a stop happened, and
  the commit step then OVERWRITES the header with "nothing was measured",
  which would be false. Section 5.
- A1. Line 1 of the landed status copy has an EMPTY sha; the new workflow
  copies that defect verbatim. Section 3.
- A2. Every refusal and every failure exits 1; the file tells them apart,
  the exit code does not. Section 5.
- A3. Nothing in the file proves the new process loaded the new code.
  Section 6 says what does, and orders it printed.
- A4. Comments in both new files describe the 5 second design; they follow
  the amendment.

What was asked and is upheld: one implementation of the three-way process
read, dot-sourced from both callers, with the query-failed outcome kept
apart from found-none (section 1); the account gate (section 5); the
evidence file staged by name beside the status copy (section 5); the
give-up arithmetic for one deliberate stop (section 2); the lint naming the
new workflow.

## 0. What was read, what was not run, and what decided it

No shell, no git, no Windows in this seat. Read whole: the three new files;
`tools/runner/install-scheduled-task.ps1`; `tools/lint-bootstrap-single.py`;
`.github/workflows/ledger-install-supervisor-task.yml`; `tools/supervise.py`
(1112 lines, the ladder 126 to 201, the loop 723 to 746, `start_child` 758
to 783); `tools/runner/launch-supervisor.py`; `START EVERYTHING.bat`;
`production/pc-ops/scheduled-task-verify.txt` and `supervisor-status.txt`
as landed; the 21:57:03Z ruling by section. Read in part: `telegram-bot.py`
543 to 629 and 1091 to 1127; `outbox.py` 433 to 453, 644 to 656, 815 to 854;
`inbox.py` 618 to 697; `pc-watcher.py` 696 to 786 and its `--seconds`
default; `.git/logs/HEAD` lines 457 to 462; `ledger/verify.py` 3835 to 3878
and 5280 to 5314; `tools/docs-check.py` 95 to 145; `.claude/agent-log.tsv`
338 to 346.

NOT RUN HERE: `ledger/verify.py`, any selftest, any git command, the
PowerShell. Every line-number claim is from the files as they sit; every
claim about his machine is from the two landed evidence files.

THE THREE FACTS THAT DECIDE THIS RECORD, all printed by something other than
me:

1. `scheduled-task-verify.txt` lines 7 to 11 (the install run on `7cb06cd`
   at 21:27:34Z): `supervisorProcessesFound=4`, and the four are two
   parent-child PAIRS with the same kind each: `19712` (parent 10700) and
   `14608` (parent 19712), both `supervise.py`; `29456` (parent 14608) and
   `14548` (parent 29456), both `pc-watcher.py`. One daemon, two python
   processes, one command line.
2. `supervisor-status.txt` line 1 as landed: `# LEDGER supervisor status as
   CI read it -  @1788816460`. The commit is blank.
3. `.git/logs/HEAD` line 461: `a766deca` is the rebased form of `1246dd30`,
   "A clip needs a route AND a process that has heard of it", at
   1788819953, which is 22:25:53Z. That is the commit whose bot code the
   restart exists to load, and it is the reference of this review.

The mechanism behind fact 1, so nobody rediscovers it: since Python 3.7.2 a
venv's `python.exe` on Windows is a redirector that launches the base
interpreter as a CHILD process and waits for it (bpo-34977). The `python=`
line of the same evidence file names
`tools\voice-live\env-export\Scripts\python.exe`, a venv; `START
EVERYTHING.bat` searches that path first (line 133); `supervise.py`
spawns the bot with `sys.executable` (577, 602), which inside a
redirected interpreter is the venv path again. So the bot is a pair for the
same reason the watcher is a pair. The evidence is the listing; the
mechanism is why the listing looks like that.

## 1. Question 1: can the match hit only the bot, and what does the kill do

THE PATTERN IS TIGHT ENOUGH IN NAME AND LOOSE IN COUNT. The filter is
`Name='python.exe' OR Name='pythonw.exe'` (process-query.ps1 33 to 34), so
an editor, a shell, `pwsh`, `git` and this workflow's own steps can never
match whatever their command lines say. Among python processes, the regex
`tools\\runner\\telegram-bot\.py` matches the path anywhere in the command
line, unanchored, so `telegram-bot.py --selftest`, `--send-outbox`, or a
copy at another root (an executor worktree, a `_work` checkout) all match.
The command line the supervisor builds (602 to 603) is the interpreter and
the script path and NOTHING after it, so the end of the command line is the
discriminator that costs nothing: `telegram-bot\.py"?\s*$`. Ruled: anchor
it, and print the matched command line with spaces as `~`, so the file
shows what matched rather than a count.

THE COUNT IS WRONG FOR THE MACHINE. Given fact 1, the bot on his PC is a
redirector and its child, both `python.exe`, both matching. `restart-
telegram-bot.ps1` line 97 reads `Count -gt 1` and refuses with both PIDs
named. So the job as written refuses on the accepting case, prints
`refused-more-than-one`, exits 1, and nothing restarts. Rule 5b: the guard
was never run on the case it should pass, and the case is in the evidence
file the same builder copied the status step from.

AND THE NAIVE FIX IS THE DANGEROUS ONE. `TerminateProcess` does not cascade.
Stop the redirector (the parent) and the interpreter keeps running: the
supervisor's `Popen` handle is on the redirector, so the supervisor sees an
exit, waits 5 seconds and spawns a second bot while the first is still
polling `getUpdates` with the same token and still sweeping the outbox.
Two consumers on one token contend on the wire and two sweeps write two
receipts. Stop the interpreter (the leaf) first and the redirector exits on
its own with the child's code, which is exactly the exit the supervisor is
built to notice.

RULED, THE SHAPE OF THE MATCH. The match is a TREE, not a count:

- The matched set is M. A root is a member whose parent is not in M.
  Refuse unless there is exactly one root; name every PID and its parent
  either way, as `botTreeBefore=<supervisorPid>>` followed by the chain,
  no spaces.
- The root's parent must be a running supervisor: a member of the set
  matched by `supervise\.py|launch-supervisor\.py` (the redirector of the
  supervisor matches too, which is fine). Otherwise refuse,
  `refused-no-supervisor-above-it`, because a bot started by "START THE
  TELEGRAM BOT.bat" (line 95) has nothing above it and stopping it leaves
  him with no channel and nothing that will bring one back. In the evidence
  the real supervisor is `14608`; the watcher's redirector hangs off it, and
  the bot's will too.
- Stop leaf first (children before parents). After the leaf, wait up to 3
  seconds for the root to leave on its own and print
  `botRootExitedOnItsOwn=true`; if it is still there, stop it and print
  `botRootStopped=true`. A `Stop-Process` on a PID that has already gone is
  recorded as gone, never as `refused-stop-failed`.
- A set of one (a non-venv interpreter, which the installer's `pythonw.exe`
  path would also produce as a pair, so this is the rare case) is the root
  alone and goes through the same code.

`Get-MatchingProcesses` grows one field, `CreationDate`, for section 2; the
installer ignores it. Its Kind labelling and its `Ok=$false` path are
unchanged and correct.

`-Force` is right and nearly moot: it suppresses the confirmation for a
process not owned by the caller; here the caller is the owner
(`runnerAccount=JAFAR-DESKTOP\Jafar`, evidence line 13). The instrument is
`TerminateProcess` either way; the bot handles no signal (grep of
`telegram-bot.py` for `signal`, `SIGTERM`: nothing; only
`KeyboardInterrupt` at 1125) and reads no stop file, so nothing gentler
exists tonight. Route c in the queue is the gentle one.

WHAT IS MID-FLIGHT WHEN IT DIES, read from the code rather than guessed:

- The long poll (1095 to 1098): about 90 percent of the time. Updates the
  bot took and had not yet confirmed with the next `offset` are re-delivered
  to the new bot, which files them through `skip_backlog` (590 to 620):
  written to the inbox, summarised once, applied never. Nothing lost,
  nothing answered twice.
- A push to `pc-inbox` (`inbox.py` 631 to 693): every 120 seconds while the
  refusal pile (the previous ruling's 7d) keeps producing a changed record.
  The git commands are CHILD processes and a parent's termination does not
  kill them; a `push` in flight finishes on its own. The private index file
  `.git/ledger-inbox-index` is deleted and rebuilt at the start of every push
  (633 to 636), so a half-built one costs nothing. The watcher's index is a
  different file and is never touched by the bot.
- A receipt between the send and the write (830 then `_write` at 644 to
  649, a plain open and write, not a rename): the message is on his phone
  and no valid receipt exists, so the next bot sends it again. A truncated
  receipt fails `receipt_is_valid` (433 to 453, no `messageId`) and has the
  same outcome. Worst case one duplicate message; never a lost one; the
  window is the milliseconds after a network call.

## 2. Question 2: the supervisor will restart it, and what could stop that

ONE EXIT AFTER 36505 SECONDS CANNOT TRIP THE GIVE-UP RULE, from `note_exit`
(165 to 193): `recent` holds failure instants and `failures` was 0 at
21:27Z (`telegram-botStops=0`, status line 26), so after one exit `recent`
has one entry against `GIVE_UP_AFTER = 5`; `up >= MIN_UPTIME_SEC` (36505
against 300) sets `step = 0`, so `wait = backoff_for(0) = 5`; the return
is `retry`. The loop (729 to 741) then sees `due` and calls `start_child`,
whose only gate is `bot_ok` (579 to 584, `config.local` present:
`configLocalPresent=True`, evidence line 17), then `spawn`. `changed` is
set on both the exit and the start, so `write_status_file` runs on each of
those ticks and the status file on disk shows `telegram-botStarts=2
telegram-botStops=1` within a second of the respawn. The exit code the
status will carry is whatever Windows reports for a terminated process, a
large unsigned number or `-1`; that is the expected reading, not a fault.

WHAT CAN TRIP IT: the NEW bot dying. An import or startup failure in the
code on disk would exit within seconds, and the ladder runs 5, 15, 45, 120,
then the fifth exit inside 1800 seconds is `gaveup`, about 185 seconds after
the first respawn. That is the state in which he has no channel until he
double-clicks. Two things see it: the stability check in section 5 (the
new leaf still alive 20 seconds after it was first seen), and the status
copy taken after that (`Stops` greater than 1 is the crash loop in
numbers). If it gives up, the evidence file says so in `gaveUp=1` and the
Producer's 04:00Z brief carries route a, which the previous ruling already
dictated as the fallback.

THE CODE IN MEMORY IS NOT THE CODE I READ. The running supervisor started
at about 11:19Z (36505 seconds before the 21:27:40Z reading) from
`resync=ok/df7a7061` (status line 16), so the ladder it will execute is
`df7a7061:tools/supervise.py`. The loop, `note_exit`, `due` and
`start_child` carry no 2026-09-07 note and the day's known edits to this
file (`install_autostart`, `default_task_exists`) are elsewhere, but that is
an inference. The resident prints the diff (section 7, print 1) before
commit 2; if those four functions differ, this record is reopened, not
reinterpreted.

THE RESTART PATH HAS RUN ONLY IN FIXTURES. `start_child` and `note_exit`
ran against a real process in the selftest (1062 to 1093); the loop's
`due` to `start_child` step ran on the policy fixture only. Tonight is its
first real run, as the script's own header says, and section 5 makes the
job report that outcome as a measurement rather than a guess.

## 3. Question 3: two writers of one file

THE SNAPSHOT CANNOT DESCRIBE A MOMENT NOBODY MEASURED. Both steps copy the
supervisor's file verbatim under a header stamped with the instant CI read
it, and `statusAgeSec` is the runner's UTC clock minus the file's UTC
mtime on the same machine, so it is the supervisor's write cadence, honest
on both copies. "Whichever ran most recently is fresh" is true of the
`@stamp`, and false of one line a reader might reach for instead:
`written=2026-09-07T23:27:16` inside the body is his PC's LOCAL time
(`time.strftime` with no zone, `supervise.py` 540) against a UTC stamp two
hours earlier. Named here so nobody computes an age from it.

THE FIRST LINE NAMES NO COMMIT, A1. Fact 2. The pwsh status step runs `git
rev-parse --short HEAD` (install workflow 173, restart workflow 137) with
none of the `GIT_CONFIG_*` trio the bash steps set, in a `_work` checkout
git already refused once for dubious ownership (the install workflow's own
comment at 134 to 143), so the sha comes back empty and the header says so
by saying nothing. The restart step already does this right with
`$env:GITHUB_SHA` (100 to 101). Ruled: both status steps use
`$env:GITHUB_SHA`, one line each; the install workflow is already in this
batch.

THE RACE IS REAL AND IT IS THIS LANDING, B3. The batch edits
`ledger-install-supervisor-task.yml` and `install-scheduled-task.ps1`, both
in the install workflow's `paths`, and adds `ledger-restart-telegram-bot.yml`,
in its own. One push, two runs. A single runner serialises them; it does not
reconcile them. The second job checks out the push sha, rewrites
`supervisor-status.txt` from that base, commits, and `git pull --rebase`
meets the first job's commit that rewrote the same file from the same base:
line 1 alone (different `@stamp`) is an overlapping hunk, the rebase
aborts, three pushes are refused as behind, and the step ends on "committed
locally on the agent". If the restart job runs second, the file that says
whether a process on his machine was killed is the one that dies. Beyond
tonight, `process-query.ps1` sits in BOTH path lists, so an edit to a
comment in the shared helper both restarts his bot and races the two
writers. Section 4 removes the cause; section 8 sequences tonight.

## 4. Question 4: the trigger, answered plainly

`workflow_dispatch` ALONE IS NOT AVAILABLE FROM THIS BRANCH. GitHub raises
the dispatch event only for a workflow that exists on the default branch;
both workflow headers say so and they are right. So the question is not
push or dispatch; it is WHICH push.

A PUSH TO THE SCRIPT'S OWN PATHS IS THE WRONG DEFAULT for a job whose
effect is killing a process on his machine: a comment edit, a refactor of
the shared helper, or a rename becomes a restart nobody decided. Ruled: the
push trigger fires on ONE path, `production/pc-ops/telegram-bot-restart.request`,
and on nothing else; `workflow_dispatch` stays for the day the file reaches
main. The request file's content is the reason, one line, no spaces
(for example `reason=load-a766deca-clip-code date=2026-09-07`), and the
job prints it as `requestReason=` in the evidence. A restart is then a
deliberate, dated, named act in a diff, and the script paths can be edited
without touching his process. The three script paths leave the trigger
list. This is the same shape the Unreal probe's sentinel takes, for the
same reason.

SHOULD LANDING RESTART HIS BOT AT MIDNIGHT WITH NOBODY PRESENT? The
previous ruling decided yes (section 5, "b tonight") with route a written
into the 04:00Z brief if b has not landed with evidence. That call stands;
this record does not reopen it. What this record changes is that the
restart is not a side effect of the landing: commit 1 carries the code and
fires only the installer, whose read-only path is the live accepting test
of `Get-MatchingProcesses` on his machine and repeats the listing section 1
relies on; commit 2 is the request file, pushed only after commit 1's
evidence has landed. The downside stays what it was: if the new bot does
not stay up, he has no Telegram until he double-clicks, and that state must
be in the brief in words. The amendments in sections 1, 2 and 5 exist so
that state is printed rather than inferred.

## 5. Question 5: refusals, exit codes, and the evidence of a destructive step

THE REFUSALS ARE DISTINCT IN THE FILE. `restartAction=` takes
`refused-account-mismatch`, `refused-query-failed`, `refused-none-found`,
`refused-more-than-one`, `refused-stop-failed`,
`stopped-but-verify-query-failed`, `stopped-but-did-not-come-back`,
`restarted`; each is one grep. The query-failed outcome is never folded
into found-none, before or after the stop (80 to 85, 125 to 135). The
account gate runs first (68 to 75) and prints both names either way.

THEY ARE NOT DISTINCT IN THE EXIT CODE, A2. All seven non-success paths
exit 1, so `restartExitCode=1` means both "nothing was touched" and "his
bot was stopped and has not been seen since". Ruled: 0 restarted and
stable; 2 refused, nothing touched; 1 a stop was attempted and the return
was not confirmed. And every path prints `botStopped=true` or
`botStopped=false` as its own line, so a reader knows whether his machine
was changed without inferring it from the absence of `stopAttempted`.

THE WAIT IS A GUESS, B2. `WaitSeconds = 5` is `BACKOFF_FIRST` copied from
the ladder, and the ladder is not the whole delay: the loop notices the
exit up to one tick late and starts the child on the first tick at or
after `retry_at` (746, `time.sleep(1)`), so the new process appears 5 to
about 7 seconds after the kill. One query at 5 seconds is a coin flip that
prints `stopped-but-did-not-come-back` and exit 1 while the status copy a
few seconds later shows `Starts=2`. Rule 2: the number was set from a
constant, not from the series the loop produces. Ruled:

- Poll every second for up to 30 seconds and print
  `botCameBackAfterSec=N`, or `none` with `waitedSec=30`. A measurement,
  not a bound.
- A process is new by `CreationDate` later than the stop instant, not by a
  different PID; Windows reuses PIDs. Print `botStopInstant=` and the new
  root's `CreationDate`.
- Then wait 20 seconds and query again: the same tree (same PIDs) still
  present prints `botNewTreeStableForSec=20` and is the success line; a
  changed or absent tree prints `botNewTreeStableForSec=none` and exits 1,
  because a bot that came back and died is the crash loop of section 2, not
  a restart. Print `botTreeAfter=` in the same form as before.
- `botNewPid` is the new leaf; `botPidChanged` stays for readers who
  already look for it but is no longer the verdict.

THE DESTRUCTIVE STEP'S EVIDENCE CAN BE ERASED, B4. Workflow line 111
assigns the child's whole output to a variable and writes it at 113, after
the child has exited. A step timeout (5 minutes, line 94) or a hung CIM
query after the stop leaves the file holding the header only; the commit
step then finds no `restartExitCode=` and OVERWRITES it (183 to 186) with
"Nothing was measured on this commit", after a process on his machine was
in fact stopped. Ruled: every line the script prints reaches the file as it
is printed (a pipeline that appends per line, with the child's exit code
read after it), and the fallback in the commit step APPENDS one line, "the
restart step did not reach its end (outcome: ...)", never replacing what
was already written. The header stays first; the two evidence files stay
staged by name (189, 193), which is correct and matches what the two
steps write (98, 134).

## 6. Question 6: what proves it worked end to end

`botPidChanged=True` proves a process exists that did not before. It does
not prove the process is the bot's, that the supervisor spawned it, that
it loaded today's code, or that it can send a clip. Each of those is a
separate measurement, and the honest strongest set before any clip goes is:

1. IT IS THE BOT AND THE SUPERVISOR SPAWNED IT: the tree of section 1, with
   the root's parent in the supervisor set, before and after.
2. THE DISK HELD THE CODE WHEN IT WAS SPAWNED: `stableHead=<sha>` from
   `git -c safe.directory=* -C C:\Users\Jafar\wc26-picks rev-parse HEAD`
   (read-only; `rev-parse` takes no lock, so it is not a second writer on
   the watcher's index), printed before the stop and after the return, and
   `botSourceSha256=` and `outboxSourceSha256=` from `Get-FileHash` of
   `tools\runner\telegram-bot.py` and `tools\runner\outbox.py` at the stable
   path, printed at the same two moments. The resident compares the hashes
   with `sha256sum` of the same files at `a766deca` in the container, and
   checks `git merge-base --is-ancestor a766deca <stableHead>`. The watcher
   resets the stable checkout within about a minute of a push (`--seconds`
   default 60, `pc-watcher.py` 1392; `resync` 716 to 740), and `a766deca`
   landed at 22:25:53Z, so the expected reading is `a766deca` or a
   descendant; a reading older than that means the watcher is not
   resetting, which is its own finding.
3. IT STAYED UP: `botNewTreeStableForSec=20` and, in the status copy taken
   after it, `telegram-botStarts=2 telegram-botStops=1 gaveUp=0`.
4. IT CAN SEND A CLIP: only `receipt: sent-with-clip` on `pc-inbox` for the
   clip message, after that message is committed. No artifact short of the
   receipt proves the send, and the previous ruling's section 5 item 4
   already accepts the restart job's file with `botNewPid` set as the gate
   for committing item 2. With this record, the gate is items 1 to 3 above
   in one file, and the receipt is the proof.

Nothing the bot prints at startup identifies its code (`hello` at 584 to
588 prints the account name only), so item 2 is what stands in until route
a in the queue gives the bot a digest of its own modules.

## 7. The amendments as behaviour, and what the resident prints

B1, `tools/runner/restart-telegram-bot.ps1` and `process-query.ps1`, BLOCKS.
Section 1: the anchored pattern; the tree; exactly one root; the root's
parent in the supervisor set; leaf-first stop with the root's own exit
recorded; `botTreeBefore=`, `botTreeAfter=`, the matched command line;
`CreationDate` in the shared query.

B2, the same script, BLOCKS. Section 5: the one-second poll to 30 seconds
printed as `botCameBackAfterSec=`, newness by `CreationDate`, the 20 second
stability check as the verdict, exit codes 0, 2, 1 as ruled, `botStopped=`
on every path.

B3, `.github/workflows/ledger-restart-telegram-bot.yml`, BLOCKS. Section 4:
`paths` is the request file alone; `workflow_dispatch` stays;
`requestReason=` printed from the file into the evidence; the header's
"push on its own paths" paragraph rewritten to say why the sentinel.

B4, the same workflow, BLOCKS. Section 5: per-line streaming of the
script's output into the evidence file; the fallback appends and never
overwrites.

A1, both workflows' status steps: `$env:GITHUB_SHA` on line 1, with the
same `SHA-UNKNOWN` fallback the restart step uses.

A3, the script: `stableHead=`, `botSourceSha256=`, `outboxSourceSha256=`
at both moments, section 6.

A4, the script header and the workflow comments: the wait described as
measured, not as 5 seconds.

The installer's re-scope, the lint entry and the install workflow's
`paths` addition of `process-query.ps1` are accepted as they are.

Before commit 1 the resident prints:

1. `git diff df7a7061 HEAD -- tools/supervise.py | grep -n "^[-+]" | grep -v "^[-+][-+]"`
   restricted by eye to `note_exit`, `due`, `start_child` and `run`: the
   ladder the running supervisor will execute is the one section 2 read.
   Any difference there reopens this record.
2. `grep -n "\\\\s\*\\$\|CreationDate\|botTreeBefore\|botRootExitedOnItsOwn\|botCameBackAfterSec\|botNewTreeStableForSec\|botStopped=\|stableHead=\|botSourceSha256" tools/runner/restart-telegram-bot.ps1 tools/runner/process-query.ps1`:
   every key at its line.
3. `grep -n "paths:" -A 2 .github/workflows/ledger-restart-telegram-bot.yml`:
   exactly one path, the request file, and
   `grep -c "GITHUB_SHA" .github/workflows/ledger-restart-telegram-bot.yml .github/workflows/ledger-install-supervisor-task.yml`:
   2 and 1.
4. `python3 tools/lint-bootstrap-single.py` and `python3 tools/docs-check.py`:
   green, with their counts.
5. `sha256sum tools/runner/telegram-bot.py tools/runner/outbox.py`: the two
   values the restart job's hashes must equal, kept in the commit message
   of commit 2.
6. `ls production/pc-ops/`: no request file yet.
7. `python3 ledger/verify.py`, footer FROM `ledger/.verify-footer`; the
   cadence line names this record and row `2026-09-07T22:52:34Z`.

Before commit 2 the resident prints:

8. `production/pc-ops/scheduled-task-verify.txt` on the branch with commit
   1's sha on line 1, `supervisorQueryOk=true` three times, and the
   listing: the pairs of section 1 again, or a different shape, which is
   read before the request file is written.
9. The commit 1 sha captured BEFORE its push, and the install run watched
   by ancestry.

## 8. The landing order, and what is armed

COMMIT 1: every file in this batch except the request file. It fires the
install workflow only (the restart workflow's single path is not touched).
The install run is read-only on his machine tonight (a supervisor is
running, so `resyncAction=skipped-supervisor-running` and
`startedNow=refused`, as at 21:27Z) and its listing is the live accepting
test of the shared query before anything relies on it to kill.

COMMIT 2: `production/pc-ops/telegram-bot-restart.request`, one line. It
fires the restart workflow only. The turn that pushes it arms a one-shot
about four minutes out that reads `production/pc-ops/telegram-bot-restart.txt`
for commit 2's sha and does one of two things: on `restartAction=restarted`
with `botNewTreeStableForSec=20`, `stableHead` at or after `a766deca` and
matching hashes, commits the clip message of the previous ruling's section
5 item 2 and arms the receipt watch; on anything else, writes the finding
into `production/NOW.md` and into the Producer's 04:00Z brief with route a
in words. Nothing here ends on "then send the clip".

THE WORDS MESSAGE IS NOT IN THE WAY. `production/outbox/` holds exactly one
walk file, `2026-09-07-the-walk.answer.md`, with no sidecar, as section 5
item 1 ordered; a plain text message is sent identically by the old code
and the new, and a kill between its send and its receipt costs one
duplicate at most (section 1). Its receipt lives on `pc-inbox` first and is
not in this checkout; the resident reads it there, not here.

## 9. Filed and waiting (names, not work)

a. THE EVIDENCE COMMIT SHOULD NEVER NEED A THREE-WAY MERGE. Both workflows
   commit on the push sha and rebase; an evidence writer that fetches the
   branch tip, resets onto it, restores its own two files and commits
   cannot conflict, because its files are whole-file overwrites. One
   change, both workflows, after tonight.
b. THE SUPERVISOR'S OWN STATUS COULD NAME THE PROCESS TREE. `key_values`
   could carry each child's PID; the copy would then say which PID is the
   bot without a CIM query, and the restart job's parent check would be a
   comparison against the supervisor's own word.
c. THE PAIR IS A COST ON EVERY LISTING. The installer's `supervisorProcessesFound=4`
   is two daemons. A `Kind` reader that collapses a redirector and its child
   into one row, or a launch through the base interpreter, ends the double
   counting; the previous ruling's 7a (the bot restarting itself on a
   source change) is still first in the queue, and it makes this whole job
   the fallback rather than the route.
d. THE `written=` LINE IS LOCAL TIME. `supervise.py` 540 could write UTC
   and say so; then the status file carries one clock, not two.

<!--RULING spawn=2026-09-07T22:52:34Z-->
