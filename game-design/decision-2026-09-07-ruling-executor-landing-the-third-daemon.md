# Ruling: the executor landing (the third daemon, rule one). LAND WITH AMENDMENTS

> **STATUS: LOG, 2026-09-07. NOT CURRENT** once the amended commit lands.
> Director ruling at spawn 2026-09-07T00:07:11Z on the uncommitted tree
> after `e70ddcc1`: `tools/runner/executor.py` (new, 1796 lines, never run
> where it matters), `tools/supervise.py` (a third child), `ledger/verify.py`
> (the selftest row), and comment-only edits to `START EVERYTHING.bat` and
> `tools/runner/run-night.ps1`. Escalated because it is a daemon that invokes
> an LLM unattended and pushes branches. From the landing on, the files are
> the reading copies and this is the record of why.

VERDICT: LAND WITH AMENDMENTS. Six block the commit, because each is a way
the first unattended run on his PC ends in silence or a false sentence on
his phone, and the whole point of this landing is that the first run is the
accepting case:

- A1. One outbox name cannot carry two messages. The limit-pause note and the
  final answer are written to the same `<stem>.answer.md`, and the sweep
  skips any name that already has a receipt, so on the exact path the limit
  handling was built for the answer is never sent. Section 4.
- A2. The lock heartbeat stops for the whole session, and STOP is ignored
  during a pause. Section 2.
- A3. Exit 0 is never a session limit. A short true answer about limits is
  today paused for eleven and a half hours and closed with a message saying
  the allowance ran out. Section 5.
- A4. `place_answer` creates the worktree path as plain directories before
  the worktree exists, and `worktree_ready` then refuses that path for ever.
  Section 3.
- A5. The docstring says the answer copy in the worktree is committed and
  pushed; only the journal is. The studio can read that he was answered and
  never what he was told. Section 3.
- A6. On Windows, `Popen(["claude", ...])` does not find an npm `claude.cmd`
  that `shutil.which` does, and the prompt's own markers carry `<`. Section 2.

A7 to A10 ride the same builder pass and do not block on their own (section
10). Everything else lands as read: the bounds, the journal, the worktree
design, the register in the prompt, the fallback wordings, the supervisor
row, the verify row, the two comment edits. `production/next-three.json` and
`tools/map.py` are not ruled on here.

NOTHING HERE HAS RUN ON JAFAR'S PC. There is no `claude` CLI, no PowerShell
and no Windows in this container. `production/outbound/` does not exist, so
zero messages have ever been delivered to him by any path, and
`tools/inbox-read.py` reports nothing tapped on the branch, so none has ever
arrived. The 82 green checks are the policy, the arithmetic and the wordings,
held against the real checker; section 9 lists what they cover and what they
cannot. The first double-click is the accepting case for the rest, and after
these amendments its failure modes are noisy rather than silent, which is the
most that can be ruled from here.

## 0. What was read, what was not run, and what I was told

Read whole: `tools/runner/executor.py` (1796 lines, two pages);
`tools/supervise.py` (1007); the three sections of `tools/runner/outbox.py`
that the executor depends on (`kind_of_name`, `outbox_files`, `receipt_rel`,
`run_check`, `sweep`, 100 to 565); `tools/runner/inbox.py` 200 to 280, 373
to 432 and 716 to 727; `tools/runner/telegram-bot.py` 614 to 746;
`tools/pc-watcher.py` 524 to 527 and 696 to 818; `tools/producer-check.py`
175 to 299; `ledger/verify.py` 1090 to 1172 and 5212 to 5306; every `on:`
block under `.github/workflows/` by grep; `.gitignore` by grep; `START
EVERYTHING.bat` and `tools/runner/run-night.ps1` whole; the inbox and outbox
READMEs; queue 143; `.claude/agent-log.tsv` whole; `.git/logs/HEAD` 428 to
435; the ruling of 2026-09-06T15:38:47Z for shape and the head of
2026-09-06T19:27:18Z.

NOTHING WAS RUN. No shell. The verify numbers are the coordinator's, quoted:
`executor selftest: 82 passed, 0 failed (of 82 case(s))`, and the one red,
`DIRECTOR NOT SPAWNED: 1928 changed line(s) (133 tracked + 1795 untracked in
1 new file(s)) vs 100 threshold`, which this record's stamp clears. The split
is the shape of the batch: the daemon is the untracked 1795, the tracked 133
are its registration.

Two facts in this record come from outside the repository and are marked as
such where they are used: what `claude -p` does with tools that need
permission when no permission flag is given, and how Windows resolves a
`.cmd` shim for `subprocess.Popen`. Neither can be checked here. Both are
stated as the first-run readings they are.

PREMISE, CLAUDE.md section 0: nothing purchased, no licence entry, no account
used by anything here (the bot is the one sender, the executor leaves a file
for it). The daemon serves the method half of the goal, "one person directing
AI agents", and Jafar's standing order that a message from his phone is
handled without him opening Claude Code. Nothing here contradicts the premise.

## 1. The reference and the stamp

The reference is `e70ddcc1`. `.git/logs/HEAD` line 435 shows it arriving as a
fast-forward from `85b5222a`, whose own commit line (434) is at 1788724345,
which is 2026-09-06T19:52:25Z; the fetch that brought `e70ddcc1` is at
1788727155, 20:39:15Z. So the reference sits between those two instants.
Studio-director rows in `.claude/agent-log.tsv` newer than either: line 318,
`2026-09-07T00:07:11Z`, and no other. Line 311 (19:27:18Z) is older than
both and is already stamped by the ruling of that name. ONE stamp, at the
foot.

## 2. Question 1: can it run away, spend without bound, or push where it should not

THE FOUR BOUNDS, each read at the line that enforces it or does not.

One instruction at a time. `pass_once` (1355 to 1386) takes `rows[0]` and
`handle` is synchronous; the lock (1041 to 1073) refuses a second executor
whose heartbeat is fresh. ENFORCED, with the hole below.

Sixty turns. `claude_argv` (826 to 834) passes `--max-turns 60`. That bound
is the CLI's, not this file's; nothing here counts turns. Written down and
handed over, which is the most a wrapper can do, and it is the same handover
`run-night.ps1` line 56 makes.

Thirty minutes. `run_session` (862 to 914): `proc.communicate(timeout=wall)`,
then `kill_tree`, then a thirty-second drain. ENFORCED HERE, and the selftest
runs it on a real process with `wall=1` (1763 to 1771). The Windows branch,
`taskkill /F /T`, has never run; on a machine where it fails the session
outlives its bound but not its turn cap.

Five pauses. `handle` 1252 to 1258: `pauses` increments, `> LIMIT_MAX_PAUSES`
gives up on the sixth limit; each wait is the ladder (30, 60, 120, 240, 240
minutes) or a parsed reset clamped to five minutes and six hours. ENFORCED.
Worst case for one instruction, from the numbers: six sessions of thirty
minutes, five waits of six hours, one repair session of ten minutes, so
three hours and ten minutes of session time inside thirty-three hours of
wall. Bounded. Every retry after a pause starts the session from nothing,
so work done before the limit is repeated, not resumed; that is the next
rung (section 8), not a fault.

The stream. One session per message he sends; `MAX_AGE_SEC` drops anything
older than a day; the first start records the backlog and runs none of it
(1150 to 1170). No per-day cap on instructions and none is needed: each is
his own message, and the bot's chat check (its docstring at 762, read, not
traced) is what stands between a stranger and a session on his PC.

THE HOLE IN THE FIRST BOUND, A2. `lock_beat` runs at the top of each pass
(1414) and inside `sleep_through` (1345). It does not run while
`proc.communicate` blocks, which is the whole session, up to thirty minutes.
`LOCK_STALE_SEC` is 135 seconds. So for all but the first two minutes of
every session the lock reads as dead, and a second executor takes it
(`lock_take` 1055 to 1061). Neither `START EVERYTHING.bat` nor
`supervise.py` has a single-instance guard, so a second double-click is a
second executor. What the second one does, read from `run` (1401 to 1410):
`close_unfinished` finds the running instruction `taken`, closes it as
`interrupted`, sends him the interrupted note, then takes the next
instruction into the same worktree while the first session is still in it.
That is the one thing the lock's docstring says must never happen, and the
guard is off exactly while it matters. RULED: the session wait becomes a
loop that beats the lock and reads the STOP file on every slice, with the
session's output going to the log file directly rather than through a pipe
(behaviour in section 10). The same loop makes STOP a kill switch that
works mid-session; today it is read only between instructions (1358) and
during a pause.

STOP DURING A PAUSE, also A2. `sleep_through` returns False on STOP (1347)
and line 1273 discards the return value: the pause ends early and the
session is re-run at once. So a STOP file placed to protect the allowance
spends it, up to five times in quick succession, then gives up with a
message saying the allowance ran out repeatedly. RULED: honour the value.

PUSHING. `push_branch` (729 to 742) pushes `HEAD:refs/heads/exec/<stem>`,
never forced, through `git_call`. The stem is the inbox filename,
`YYYY-MM-DDTHHMMZ-<update>` (inbox.py 200 to 202), a legal ref name. It
cannot name the work branch. No workflow triggers on the branch name: every
`push:` block under `.github/workflows/` is either `branches: [claude/...]`
or path-scoped with no branch filter. The path-scoped ones are what rule 9
asks about: `ledger-core-tests` (`ledger/**`, `game-design/**`, cheap by its
own header), `ledger-ai-playtest` (`ledger/Assets/Scripts/Core/**`), and the
four sentinel files under `production/d1-probe/` that dispatch imagegen,
vignette fetch, MSVC setup and the Unreal probe. A session that edits one of
those and commits has its push dispatch that run, on the stream with the
concurrency limit. The daemon cannot know; the session does what he asked.
RULED acceptable for this landing with the fact on the record, and the
journal line that names which trigger paths a push touched is filed (section
12, c), so the day it happens the record says so before anybody asks.

THE PROMPT IS NOT A BOUND, and the record has to say what that means. The
session is told not to push and not to open a pull request (773 to 774).
With the CLI's default permissions in print mode, my understanding from
outside this repository is that tools which write or run are refused and
read-only tools are allowed, so the first run answers questions and does no
work, and "commit what you change" in the prompt is a sentence the session
cannot obey. The escape hatch is `claude-args.txt` in the state directory
(809 to 823), and the flag that goes there is the one decision that turns a
question-answerer into a worker with a shell. That is Jafar's machine and
his call; the record's job is to say that the choice exists, that it is
made in a text file outside the repository, and that once made the prompt's
"do not push" is a request to a model with a git client. A7 puts the one
sentence into the prompt that today is missing: the checkout one level up
belongs to another process. It is not a guard. Nothing here can be.

WINDOWS INVOCATION, A6. `run_session` checks `shutil.which("claude")` and
then spawns `["claude", ...]` (874 to 888). `which` honours PATHEXT and
finds a `claude.cmd`; `Popen` with a bare name does not (outside knowledge,
the common experience with npm shims on Windows). On that install the
daemon reports the CLI found in its status line and then answers every
instruction with the no-tool fallback, which says the tool is not on the
machine. Noisy and wrong. And the prompt's markers `-----8<-----` carry `<`,
which cmd.exe reads as redirection when it re-parses a `.cmd` file's
arguments. RULED: argv[0] is the resolved path; the markers are letters and
`=`. What remains a first-run reading: `%` and `!` inside his own text on
that shim.

## 3. Question 2: the checkout ownership guard

EVERY SUBPROCESS SITE IN THE FILE, by grep: 630 (`git_call`), 661 (`git
worktree add`, in the repository root, direct), 847 (`taskkill`), 883 (the
session), 1753 and 1764 (selftest fixtures, python). So there is exactly one
git invocation outside `git_call`, and it is the one the docstring at 646
to 651 declares. What it does: `git worktree add --detach <path> HEAD` with
`cwd=repo`, only when `<worktree>/.git` is absent (653 to 655). It reads
HEAD, writes `.git/worktrees/<id>/` and the new directory. It does not
fetch, does not read FETCH_HEAD, does not touch the index or the working
tree the watcher resets. It is not the hazard the guard was built for
(`pc-watcher.resync` 716 to 740: fetch, `rev-parse FETCH_HEAD`, `reset
--hard`). RULED: the guard holds for its hazard. The sentence "no git
outside `git_call`" is false by one documented, once-only, non-fetching
command, and the docstring says so; that is the honest state and it stays.

THE MODULES IT CALLS, because a guard by path in one file can be walked
around by an import. From the executor: `inbox.message_files` (a directory
listing, 251 to 262), `parse_message` (pure), `one_line`, `render_message`,
`message_name` (pure); `outbox.run_check` (runs `producer-check.py` with
`cwd=repo`, no git, 326 to 351), `kind_of_name`, `outbox_files`,
`outbox_rel`. `outbox.commit_epoch` does run `git log` in the root through
`inbox.git_call`, and it is called only from `sweep`, which is the bot's.
No second git path from this daemon.

THE SHARED STATE A WORKTREE FETCH DOES TOUCH, said so it is not discovered
later: `refs/remotes/origin/<branch>` is common to both checkouts, and the
executor's `fetch origin <branch>` (686) moves it. The watcher's resync does
not read that ref (it reads its own FETCH_HEAD and runs `merge-base
--is-ancestor HEAD <sha>`, 763 to 771). `inbox.newest_work_commit` (375 to
393) does read it, for the bot's awake/asleep sentence, and an earlier fetch
makes that reading fresher, not falser. Two fetches colliding on a ref lock
fail one of them with a message, and both callers retry on their next pass.
FETCH_HEAD itself is per-worktree, which agrees with the builder's stated
measurement on git 2.43 and with git's own layout; I cannot re-measure it
here.

THE GIT THE GUARD CANNOT SEE is the session's. A session with a shell is a
git client whose parent directory is the watcher's checkout, and nothing in
the prompt names that directory as off-limits. A7.

TWO FAULTS IN THE WORKTREE HANDLING, both blocking because each is a first
run that ends in a permanent wrong state.

A4. `place_answer` (940 to 963) writes the second copy under `self.worktree`
with `os.makedirs`. `deliver` calls it from `close_unfinished` at start
(1179), before any worktree exists, and from every `no-cli` and `failed`
path in `handle`, including the one where `worktree_ready` has just refused
(1213 to 1217). `worktree_ready` line 656: a path that exists, is non-empty
and has no `.git` is refused, every time, for ever. So: git not yet on PATH
on the first instruction, the no-tool note is delivered, `../ledger-exec/
production/outbox/` now exists as plain directories, git is installed, and
every instruction from then on is answered "not set up on this machine
yet", with the reason only in a status file. RULED: the worktree copy is
written only when `<worktree>/.git` exists; otherwise the count says one
copy and the journal says why.

A5. The docstring at 944 to 947: the worktree copy "is committed and pushed,
which is the only route the studio in the container has to read what was
said." `commit_record` (701 to 726) stages one named file, and `push_record`
(1318 to 1339) names `production/executor/journal.log`. Nothing stages the
answer. The exec branch carries `answer-placed ... chars=N` and never the
text. Rule 1: the comment claims what the code does not do. RULED: the
answer files delivered for the instruction are staged by name beside the
journal, and the docstring becomes true.

## 4. The sweep, and why the recognised limit path is the silent one

This is A1 and it is the finding that matters most. `deliver` (1184 to
1202) writes every message for an instruction to `outbox_rel(stem)`, which
is `production/outbox/<stem>.answer.md` (299 to 310): the pause note (1270),
the interrupted note (1179), the give-up note (1256), the register fallback
(1309) and the answer (1297). `outbox.sweep` 459 to 465: a file whose
receipt exists and is valid is `already` and skipped; the receipt is named
from the file (147 to 148). The sequence on a real limit: pause note
written, bot sends it within two minutes, receipt written; wait of at least
five minutes (the clamp floor) or thirty (the ladder); session re-run;
answer written to the same name; sweep reads the receipt; answer never
sent. He is told "it starts again by itself, you do not need to do
anything", and then hears nothing, ever. The journal on the exec branch says
`answered`. That is fail-silent on the one path the limit machinery exists
for, and no selftest case walks it because the selftest never sends twice
under one name.

RULED: the pause note takes its own name, `<stem>.paused.answer.md`, so the
final message of the instruction is the only thing ever written to
`<stem>.answer.md`. `kind_of_name` matches on the suffix (112 to 118), so
the sweep still knows the register; `record_base` gives it its own receipt.
One selftest row plants a receipt for `<stem>.answer.md`, delivers a pause
note, and asserts the pause note's name is not the receipted one; one row
asserts that after a pause the final answer's name carries no receipt. Both
run in the container.

## 5. Question 3: the limit is a guess, and which way it fails

WHEN THE WORDING IS ONE NOBODY PREDICTED. `looks_like_limit` returns False,
`handle` breaks (1247), the notice becomes the draft, the register almost
certainly passes it (the checker allows clock times and durations in the
answer register, `COUNTS_ALLOWED_IN`), and the notice goes to his phone
with the board link under it. The instruction is closed `answered` and the
journal carries `code=` and `firstLine=`, the exact words (1242 to 1246).
So: he sees the CLI's own sentence, he knows the thing did not run, and the
next session sets the pattern from the journal. FAIL-NOISY, and RULED
acceptable. The turn cap ends the same way, with the CLI's words as the
answer. Noisy, and acceptable for a first run whose purpose includes
learning those words.

WHEN THE WORDING MATCHES BUT IT WAS NOT A LIMIT, A3. `looks_like_limit` 413
to 418: on exit 0 the only defence is length; a short exit-0 output with a
matching phrase is a limit. "You have not reached your usage limit." is a
short, true, exit-0 answer to a question he could well ask, and it matches
`reached-your-limit`. What follows, read from `handle`: the pause note goes
to him ("the allowance on the account ran out part way through"), the
ladder waits 30, 60, 120, 240, 240 minutes while the same answer is
produced five more times, and after eleven and a half hours he gets the
give-up note. A false statement about his account, delivered as fact, with
the true answer thrown away six times. Against it, the case the exit-0 rule
protects: a CLI that prints a real limit and exits 0. That case falls into
the paragraph above, noisy and truthful, and the journal's `code=0
firstLine=...` is the evidence that sets the rule next time. RULED: exit 0
is never a limit. The selftest's `reject/a-long-successful-answer...` row
becomes "any exit-0 output", and the `accept/but-the-same-words-on-a-FAILED-
exit` row stays. Same pass: the repair session's output is used whenever it
started and is non-empty (1305); on a non-zero exit its output is a notice
or a stack trace and must not become his answer, so a non-zero repair exit
goes straight to the fallback.

ONE MORE ON THIS AXIS, A9. `compose_answer` returns the empty string when
the session text is empty, BEFORE it appends the note (330 to 334). In print
mode the CLI prints its final message at the end, so a session killed by the
wall clock has most likely printed nothing, and the draft is empty. `handle`
then sends `EMPTY_NOTE` ("produced no answer to send") instead of
`TIMEOUT_NOTE` ("reached the time limit"). Two different facts, and the
wrong one goes. RULED: a timed-out session with no text sends the timeout
note.

WHAT THE SIX PATTERNS ARE. A guess, said so in the code (202 to 207), and
the journal's `firstLine` is the instrument that replaces the guess. That is
the right shape for a bound nobody has measured, and it stays.

## 6. Question 4: the answer register can refuse the answer

THE JUDGMENT ASKED FOR. The register is right for this channel and it stays
as it is. The reader is Jafar, on his phone, and he ruled the register: the
banned words (producer-check 257 to 262) are the words of the studio's
plumbing, and an answer that needs "workflow", "dispatch", "verdict" or a
file path to be true is an answer written for an engineer. His most useful
questions are answerable without them. "Did last night's run work?" is
answered by "The street got its surface back last night; the two pictures on
the board show brick where there was grey, and tonight's run is the next
test." Not one banned word, and it is the Producer's register exactly. The
prompt carries the ban (781), the selftest holds the prompt's list against
the real checker (1498 to 1506), and the repair pass carries the refused
clause back to the model (789 to 806). That is a good second rung and it
stays.

WHERE THE REGISTER IS WRONG, and it is one case: the words he typed. If he
asks "which branch is the map on?", no answer can say "branch", and the
fallback tells him the answer could not be put in the accepted form, which
is true and absurd. The checker already holds the principle that fixes it:
counts are legal in the answer register because "his question sets what is
answered" (184 to 186). The same principle, extended by one clause: a word
in his instruction is a word he can read in the answer. It needs the
instruction beside the answer at check time in both places the check runs
(the executor and the bot's sweep), so it is a header the answer file
carries and the checker reads. That is a change to the instrument and to
two callers, it is adjacent to this landing, and it is filed with a name
(section 12, a). It is not built here, and the register is not loosened
here.

THE FALLBACK'S CLAIM. "It is being held on the machine": true of the session
log under the state directory (`logs/<stem>-try1.log`) and of the clause in
the journal on the exec branch, so the studio can read both. Not true of any
committed copy of the draft; after A5 the fallback itself is committed, and
the refused draft still is not. That is acceptable: the draft failed the
register, and the register also governs what the work branch carries.

## 7. Question 5: one branch per instruction, for ever

Each `exec/<stem>` is the work branch's tip plus one record commit and
whatever the session committed; storage is deltas and the cost is listing
clutter and rule 9. Nothing triggers on the branch name (section 2). The
daemon's own stated property, that no push it makes can destroy anything
(729 to 734), is worth more than tidiness, so pruning is not the daemon's
job. RULED: acceptable now, no bound in this landing; the bound is a
studio-side pruning of `exec/*` branches older than fourteen days whose
journal the work branch already carries, filed (section 12, b). After A5 the
branches are also where the answer text lives, which is one more reason the
studio reads them before anything deletes them.

## 8. Scope, and the ladder

ASKED: a Telegram instruction becomes a real session and the answer comes
back on his phone without him opening Claude Code. Every file in the batch
is that. The two comment edits are the right size for what they say.

ADJACENT, named and not done here: the words-he-typed exemption (a), the
pruning (b), the trigger-path line on each push (c), the bot's reply naming
the PC's own handler (d), a single-instance guard on the supervisor (e), an
orphan-session kill on restart (f), and `git clean` in the worktree before a
session (g). Section 12.

THE LADDER. The route is best available for a daemon nobody has run: the
journal outside both checkouts, `taken` before anything starts, one name per
update id, the register run before placement, every wording held against the
real checker. Its next rung is not blank: resume the session after a limit
rather than restart it, so the work before the pause is kept, if the CLI on
his PC offers a resume; and the orphan kill (f). The limit recogniser is
first working by design and its next rung is the journal's own `firstLine`.
The answer register is best available for unprompted messages and one clause
short for answers (a).

## 9. What 82 green checks cover, and what they cannot

Covered, in the container, and I read the cases: the instruction filter
(1445 to 1452); composition, the cut and the link (1455 to 1474); the eight
wordings against the real checker and the prompt's ban list against it (1479
to 1506); the invocation shape against `run-night.ps1` and the args file
(1522 to 1542); limit recognition both ways and the reset parser (1545 to
1600); the journal's states and the crash-resumes rule (1603 to 1628); the
guard by path, accepting and rejecting (1631 to 1648); the lock (1652 to
1658); the status file (1661 to 1689); the inbox reader with a planted README
(1692 to 1719); the first-start backlog (1722 to 1735); placement and the
sweep finding it (1738 to 1749); a real child's output, a real wall-clock
kill, and a spawn that raises (1753 to 1781).

NOT covered, and not coverable from here: the CLI's exit code and first line
on a limit, on a turn cap and on a permission refusal; whether print mode
allows any tool without a flag; whether `taskkill /T` reaches the session's
children; whether `git worktree add` succeeds on his git; whether a push from
a linked worktree uses the same credential the watcher does; the bot's sweep
sending an `.answer.md` at all (no receipt has ever been written); and every
one of the four unmeasured policy numbers. The first instruction's journal
is the series for all of them.

## 10. The amendments, stated as behaviour

A1, `tools/runner/executor.py`, BLOCKS THE COMMIT. `answer_name(stem,
tag="")` returns `<stem>.answer.md` or `<stem>.<tag>.answer.md`; `deliver`
takes the tag; the limit-pause note is delivered with tag `paused` and every
terminal message with none. Two selftest rows as in section 4.

A2, same file, BLOCKS. `run_session` opens the log file and hands it to the
child as stdout (stderr merged), then loops on `proc.wait(timeout=slice)`
with `slice` no larger than 30 seconds; on every slice it calls an injected
`beat()` (the lock heartbeat in production) and an injected `stop()` (the
STOP file); on `stop()` it kills the tree and returns `timedout=False,
stopped=True`. After exit it reads the log back as `out`. `handle` treats
`stopped` as terminal `failed` with the interrupted note. `sleep_through`'s
False is honoured: record `stopped-during-pause`, close `failed`, deliver the
interrupted note, push the record, return. Selftest: the two real-process
rows stay; one row injects a counting `beat` under a wall of three seconds
with a one-second slice and asserts it counted at least two; one row injects
a `stop` that returns True on its second call and asserts the session was
killed and `stopped` is True.

A3, same file, BLOCKS. `looks_like_limit` returns `(False,
"it-exited-0-so-a-limit-phrase-is-prose")` whenever `exit_code == 0`,
before the pattern loop; `LIMIT_NOTICE_MAX_CHARS` and its comment go; the
selftest row at 1558 to 1562 asserts the new reason. In `handle`, a repair
result with a non-zero `rc` is not used as a draft.

A4, same file, BLOCKS. `place_answer` writes the worktree copy only when
`os.path.exists(os.path.join(worktree, ".git"))`; otherwise `copies` is one
and `say` names the skip. One selftest row on a bare directory asserts one
copy and no directory created under it.

A5, same file, BLOCKS. `push_record(branch, why, rels=())` stages the journal
and every rel in `rels` by name, in one commit; `handle` and `close_unfinished`
pass the rels `deliver` returned. The docstring at 940 to 948 is then true
and stays. One selftest row commits a journal and a planted answer rel in a
temporary repository and asserts both are in the commit's tree.

A6, same file, BLOCKS. `run_session` resolves argv[0] through
`shutil.which("claude")` and spawns the resolved path; `claude_argv` is
unchanged so the run-night comparison still holds. The two prompt markers
become `===== BEGIN INSTRUCTION =====` and `===== END INSTRUCTION =====`, and
one selftest row asserts no `<` or `>` in the prompt outside his instruction.

A7, same pass. `build_prompt` gains, after "belongs to you alone": "The
folder one level up, the project checkout, belongs to another process that
resets it every minute. Never read from it, write into it, or run anything
inside it." One selftest row asserts the sentence is in the prompt.

A8, same pass. `too-old` and an unreadable message each deliver a note; the
wordings are the builder's, held against the real checker in the selftest
like the other eight.

A9, same pass. `handle` sends the timeout note when `res["timedout"]` and the
draft is empty (section 5).

A10, same pass, the docstring at 41 to 71: "WRITES exactly two untracked
files" becomes the true count after A1 (the answer, the pause note, the
status mirror). And the module docstring's hop 7 says the answer text rides
the branch, which A5 makes true.

The builder states the new selftest count; this record does not guess it.

## 11. What the resident prints before the commit

1. The builder's diff for A1 to A10, read against sections 2 to 5.
2. `python3 ledger/verify.py`, footer pasted FROM `ledger/.verify-footer`.
   Expected: `executor selftest ok (N checks, 0 failed)` with N above 82 by
   the stated number; the cadence line pairing this record with row
   `2026-09-07T00:07:11Z`; `docs` clean with this record counted.
3. `grep -n "communicate(timeout=wall)" tools/runner/executor.py` returns
   nothing.
4. `grep -n "8<" tools/runner/executor.py` returns nothing.
5. `grep -n "paused" tools/runner/executor.py` shows the tag at the delivery
   of the pause note and in a selftest row.
6. `grep -rn "exec/" .github/workflows/` returns nothing, as it does today.
7. `ls production/outbound/` fails: the directory does not exist, and the
   commit message says so in words: zero messages delivered by any path, the
   first double-click is the accepting case, and the journal of the first
   instruction is the series every bound in this file waits on.

## 12. Filed and waiting (names, not work)

a. WORDS HE TYPED ARE WORDS HE CAN READ. The answer register exempts tokens
   present in the instruction; the answer file carries the instruction in a
   header the checker reads; both callers pass it. `tools/producer-check.py`,
   `tools/runner/outbox.py`, `tools/runner/executor.py`. Studio, small, after
   the first real refusal is on the record.
b. PRUNE `exec/*`. Studio-side, never the daemon: branches older than
   fourteen days whose journal the work branch carries. One tool, one line in
   the map.
c. THE PUSH NAMES WHAT IT TRIGGERS. `push_record` prints
   `touchesTriggerPaths=` from `git diff --name-only <base>..HEAD` against the
   path lists in the workflows. Rule 9 made mechanical.
d. THE BOT'S REPLY NAMES THE PC'S OWN HANDLER. `inbox.reply_text` appends
   the awake/asleep sentence and the next wake at 04:00 UTC; with the
   executor up, that is a second promise on the same phone, followed a minute
   later by an answer. The bot reads `executor-status.txt`'s `written=` and
   says whether the PC is handling it itself. First-run confusion, not a
   fault.
e. ONE SUPERVISOR. A heartbeat lock in `supervise.py` of the executor's
   shape, so a second double-click says so and exits.
f. THE ORPHAN. The executor writes the session's pid and start instant to
   the state directory and, on start, kills a fresh one before closing the
   instruction as interrupted. The Windows pid-reuse question is the
   builder's to answer.
g. `git clean -fd` in the worktree after the detach and before the session,
   so a previous session's untracked leftovers cannot be read as the tree.

<!--RULING spawn=2026-09-07T00:07:11Z-->
