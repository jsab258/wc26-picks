# Ruling: the installer resync, two fixes after 45de6c21. LAND WITH AMENDMENTS

> **STATUS: LOG, 2026-09-07.** Director ruling at spawn 2026-09-07T20:41:08Z
> on the uncommitted tree after `45de6c21`: 158 changed lines against the 100
> threshold, two files, 0 director rows newer than the reference before this
> one. NOT CURRENT once the amended commit lands; from then the two files are
> the reading copies and this is the record of why.

VERDICT: LAND WITH AMENDMENTS. Two block, one rides the same pass:

- B1. The resync gate names the door, not the writer. `Get-SupervisorProcesses`
  matches `supervise.py` and `launch-supervisor.py`; the process that actually
  hard-resets the index every minute is `pc-watcher.py`, which can be alive
  with no supervisor above it. And a zero from a process query that could not
  run reads the same as a zero from one that did. Section 1.
- B2. The branch the reset lands on is the workflow's ref, and the account
  that writes is whoever the runner is today. The checkout belongs to the
  daemons; the writer must be their branch and their account, or it is a
  second author. Section 3.
- A1. A failed git call discards its own reason (`2>$null`), and the reset
  says nothing about what it is about to throw away. Section 2.

The deadlock analysis is upheld: on THIS run the launcher will be at the
stable path before `Find-Repo` looks for it (section 4). The workflow's
`safe.directory` trio on the pc-inbox read step lands as read.

## 0. What was read, what was not run, and what I was told

No shell, no Windows, no git in this seat. Read whole:
`tools/runner/install-scheduled-task.ps1` (393 lines), the workflow,
`tools/runner/launch-supervisor.py`, `tools/runner/single_instance.py`,
`START EVERYTHING.bat`, `.gitignore`. Read by section: `tools/supervise.py`
(`resync_once` 439 to 478, `git_env` 428 to 436, `spawn` 611 to 616, `run`
654 to 755, `default_task_exists` 331 to 345); `tools/pc-watcher.py`
(`resync` 696 to 740, `deliver_before_discard` 743 to 786, `publish`
docstring 789 to 805, `BRANCH` 52, `RESULT` 50); `tools/runner/executor.py`
1 to 80; `tools/runner/inbox.py` `WORK_BRANCH` 51; the predecessor's record
(sections 3 and 9); `ledger/verify.py` 3838 to 3877.

THE EVIDENCE FILE WAS NOT OPENED HERE. `production/pc-ops/` does not exist
in this checkout (glob, 0 files), so the quoted lines (`MISSING ...`,
`installerExitCode=1`, `pcInboxReachable=false`) are the coordinator's,
not mine. The resident opens the landed copy (section 6).

Two facts come from outside the repository and are marked where used: the
git-reset manual's wording on untracked files in the way of a tracked path,
and PowerShell 7.1's change to native stderr under `ErrorActionPreference`.

## 1. Question 1: is "no supervisor process" a sufficient gate

THE GATE NAMES THE WRONG PROCESS. The index writer on that PC is
`pc-watcher.py` (`pc-watcher.py:696`, "hard-resets it every pass";
`executor.py:43`). A supervisor's children are `Popen` with no job object
and no creation flags (`supervise.py:611` to 616); the only path that
terminates them is `KeyboardInterrupt` (747 to 755). A supervisor that
dies any other way, and every supervisor under the task is windowless so
Ctrl-C is not how it will die, leaves `pc-watcher.py` running alone.
The pre-supervisor "START THE STUDIO MACHINE.bat" started it alone by
design. In both, the gate reads `supervisorProcessesBeforeResync=0`, the
installer fetches and resets an index a watcher is resetting once a
minute, and the evidence says the gate held. That is the four-day fight
with a line saying it was prevented. Widening the matcher costs one
token and changes no outcome in the normal state (a task-started
supervisor has all three names running; the gate already refuses).

THE ZERO HAS NO DENOMINATOR (rule 3b). `Get-CimInstance ... -ErrorAction
SilentlyContinue` (60 to 62) returns nothing both when no python runs and
when WMI could not answer. The gate then writes. The safe side of a lock
is refusal.

THE RACE, WITH BOTH FIXES IN. Window: seconds, between the CIM read and
the end of `reset --hard`. A supervisor starting inside it (logon, the
bat, or the task itself is not yet registered at that point) runs
`resync_once`: fetch, then reset, on the same repository. Git serialises
the index behind `.git/index.lock`, so the two resets do not interleave;
one exits 128. If the installer's loses: `resyncAction=failed-reset`, then
`Find-Repo`; the launcher is there if the supervisor's won, and the install
proceeds. If the supervisor's loses: `resync_once` returns false and the
supervisor starts anyway on the code on disk (`supervise.py:673` to 676);
`pc-watcher` converges the checkout within a pass. Two concurrent fetches
of one ref can collide on the ref lock; the loser prints `failed-fetch`.
The `FETCH_HEAD` race `executor.py:44` names (fetch A, fetch B, A reads
B's `FETCH_HEAD`) is benign ONLY when both fetch the same ref, which is
B2. Worst outcome with B1 and B2: one named git failure and a checkout
that is on the branch within one watcher pass. Acceptable.

## 2. Question 2: what a hard reset discards

CONFIRMED, WITH ITS EDGE. The manual (outside: git-scm.com, git-reset,
`--hard`): resets index and working tree, discards changes to tracked
files, and "may overwrite untracked files" that sit where a tracked path
is written. So:

- `ue-probe/Packaged/` (`.gitignore:105`; nothing tracked under it in this
  tree, glob 0 files) survives. `tools/voice-live/env-export/` (92) and
  `tools/runner/config.local` (98) survive. The lock, refusal file and
  launcher log under `game-design/pc-jobs/` are untracked and survive.
- `production/inbox/`, `production/outbox/`, `production/outbound/` ARE
  TRACKED on this branch: 321 files here, including
  `production/inbox/2026-09-07T0550Z-79313218.md`, while `executor.py:21`
  to 23 says inbox files are untracked on the PC. A PC copy that shares a
  name with a tracked one is overwritten by the branch's copy; the rest of
  the 254 survive. The content is the same message either way today, and
  `pc-watcher` does this every minute already; the installer adds no new
  exposure. The disagreement between the docstring and the tree is filed
  (section 7b).

TRACKED AND POSSIBLY MODIFIED THERE: `game-design/pc-jobs/result.txt` and
`request.json` are tracked. `pc-watcher` writes `result.txt`
(`pc-watcher.py:50`) and commits it to `pc-results`; a local edit is
uncommitted only if the 11:30 death fell between the write and the
publish. The local branch may also sit ONE COMMIT AHEAD of origin (798 to
800); `pc-watcher` refuses to discard that until it is on `pc-results`
(743 to 786); `resync_once` and the installer do not. `START
EVERYTHING.bat` copies `result.txt` to `~/ledger-rescued` before the
supervisor's reset for exactly this (116 to 123). The installer looks at
nothing before it destroys. A1: print what will go (dirty tracked names,
capped and announced; local commits ahead, with the head sha), then
proceed. Proceed, because refusing keeps the deadlock and the reflog keeps
the commit for 90 days under the sha the evidence names.

## 3. Question 3: the branch, and the account

RIGHT ON THIS RUN, WRONG BY DESIGN LATER. A push to
`claude/game-dev-ai-automation-2h67ix` sets `GITHUB_REF_NAME` to it, equal
to `inbox.py:51`, `pc-watcher.py:52` and `supervise.py:660`. The workflow
header (lines 24 to 27) plans the day this file reaches `main` and runs by
dispatch from there; `GITHUB_REF_NAME` is then `main`, and `reset --hard`
moves his LOCAL working-branch ref to main's tip (a hard reset moves the
checked-out branch). The supervisor's next start resets back, so it
self-corrects in one generation, but inside that generation the race in
section 1 is the "wrong tree" case and the launcher may not exist on
`main`. The checkout's branch is the daemons' constant, so the installer
writes that constant and only prints the ref.

THE SAME FOR THE ACCOUNT. CI writing to his checkout is acceptable
because, per the quoted evidence line, CI IS him
(`runnerAccount=JAFAR-DESKTOP\Jafar`). The predecessor recorded a
NETWORK SERVICE era on this machine. A fetch under any other account
writes objects into his `.git` owned by someone else, and the
`dubious ownership` guard then bites the daemons. B2: resync only when
`$env:USERNAME -eq $TargetUser`.

## 4. Question 4: does this break the deadlock or move it

BREAKS IT, ON THIS RUN. The push touches both trigger paths (workflow 39
to 40). The runner checks out the pushed commit into `_work` and runs
THAT copy of the installer, the new one. Gate reads 0 (the 11:30 death
was a console close, which takes the children with it; the orphan case is
B1). `C:\Users\Jafar\wc26-picks\.git` exists (the executor's linked
worktree hangs off it). `fetch origin <branch>` puts `FETCH_HEAD` at the
pushed commit or newer; `45de6c21`, which carries
`launch-supervisor.py` and `single_instance.py`, is its ancestor. The
reset writes them to the stable path. `Find-Repo` returns it;
`Find-Python` finds the untracked voice env; the launcher exists;
register; `Start-ScheduledTask`. The launcher is there THIS run.

Three conditions, each failing NAMED rather than green: the fetch works
under the runner (network, and credentials if the repository is private;
`GIT_TERMINAL_PROMPT=0` makes a missing credential a fast 128, not a
hang); no stale `.git/index.lock` from 11:30 (reset 128, `failed-reset`,
then `MISSING`, exit 1); no orphaned watcher (B1). The second is why A1
carries git's words: `exitCode=128` alone cannot tell a stale lock from
a permission fault from a full disk, and the evidence file is the only
channel.

## 5. Question 5: success reported over something that cannot fire

NOTHING NEW IN THIS DIFF. Every resync failure prints a named
`resyncAction=` and then trips the launcher check. One residual,
pre-existing and accepted last review with the log-file fix:
`startedNow=attempted` followed by `supervisorProcessesAfter=0` still
exits 0, because the task exists and three seconds cannot tell
"starting" from "died on its first line". The reader reads the number,
not the exit code (section 6).

ONE READING FROM THE SAME PATH, NOT THIS DIFF. A8 (`CREATE_NO_WINDOW` on
`spawn`) is not in `tools/supervise.py`: grep for `creationflags`,
`NO_WINDOW`, `08000000`, `DETACHED_PROCESS` returns nothing. Under the
task the supervisor runs under `pythonw.exe` and each child is a
console-subsystem `python.exe` with no console to inherit, so three
windows open at logon, each closeable. Not a false success; filed (7a).

THE WORKFLOW'S HALF. The trio matches the commit step and the probe;
lands as read. Note for the reader: the `_work` checkout has
`persist-credentials: false`, so if the repository is private the
pc-inbox fetch prints `pcInboxReachable=false` with an auth message, a
different fault from today's; read `pcInboxError=` before reading
`false` as a dead heartbeat.

## 6. The amendments, stated as behaviour, and what the resident prints

B1, `tools/runner/install-scheduled-task.ps1`, `Get-SupervisorProcesses`,
BLOCKS. The filter is `supervise\.py|launch-supervisor\.py|pc-watcher\.py`;
the third prints `Kind=pc-watcher.py-the-index-writer`. The CIM query runs
under `-ErrorAction Stop` inside try/catch. On success the gate line
carries `pythonProcessesExamined=N` (rows before the command-line filter).
On failure both gates refuse: `processQuery=failed reason=<msg>`,
`resyncAction=skipped-could-not-ask-windows`, and later
`startedNow=refused reason=could-not-ask-windows`; the task is still
registered and fires at the next logon through the lock.

B2, same file, BLOCKS. `$ResyncBranch` is the literal
`claude/game-dev-ai-automation-2h67ix`, the comment naming
`tools/pc-watcher.py` `BRANCH` and `tools/runner/inbox.py` `WORK_BRANCH`
as the two it must equal; `GITHUB_REF_NAME` prints as `resyncGithubRef=`
and is never passed to git. The resync runs only when `$env:USERNAME -eq
$TargetUser`; otherwise `resyncAction=skipped-runner-account-is-not-target-
user account=<COMPUTERNAME\USERNAME>` and the script continues to
`Find-Repo`, which refuses on `MISSING` as today.

A1, same file, same pass. Each git call captures stderr (`2>&1` into a
variable; under pwsh 7.1+ native stderr does not trip Stop, outside:
PowerShell PR 13361) and a failure line carries `gitSaid=<first 200
chars, whitespace to _>`. Before the reset: `resyncDirtyTracked=N` from
`git status --porcelain --untracked-files=no`, up to 10 names, `(+N more
not shown)` when capped; `resyncLocalAhead=N resyncLocalHead=<sha7>` from
`git rev-list --count FETCH_HEAD..HEAD`. The reset proceeds.

Before the commit the resident prints:

1. `grep -n "pc-watcher" tools/runner/install-scheduled-task.ps1`: the
   widened filter and its kind label.
2. `grep -n "GITHUB_REF_NAME" tools/runner/install-scheduled-task.ps1`:
   only inside a `Write-Host`, never on a git line.
3. `grep -n "USERNAME" tools/runner/install-scheduled-task.ps1`: the
   account gate before `Push-Location`.
4. `python3 ledger/verify.py`, footer FROM `ledger/.verify-footer`; the
   cadence line names this record and row `2026-09-07T20:41:08Z`.
5. The sha, captured BEFORE the push. Then watch by ancestry for the
   install run whose commit contains it, open
   `production/pc-ops/scheduled-task-verify.txt`, and read in order:
   `pythonProcessesExamined=`, `resyncAction=`, `resyncLocalAhead=`,
   `repo=`, `installAction=`, `startedNow=`, `supervisorProcessesAfter=`,
   `taskLastTaskResult=`, `pcInboxReachable=`. Green is
   `resyncAction=updated`, `installAction=create`,
   `supervisorProcessesAfter` of 1 or more. `supervisorProcessesAfter=0`
   after `startedNow=attempted` is not green whatever the exit code; the
   next signal is the pc-inbox commit age moving on a re-dispatch.
6. The Producer's message, if any, after that file has landed and says
   what the file says.

## 7. Filed and waiting (names, not work)

a. A8 DID NOT LAND. `supervise.py:611` to 616 passes no creation flags;
   three console windows at logon under the task. Queue item, with the
   selftest the predecessor specified.
b. TRACKED TWINS OF UNTRACKED FILES. `production/inbox/`, `outbox/`,
   `outbound/` tracked here (321 files), described as untracked on the
   PC in `executor.py:21`. One of the two statements changes.
c. THE INSTALLER'S DISCARD HAS NO DELIVERY STEP. A1 prints the loss; a
   rescue copy the way the bat makes one (116 to 123) is the next rung
   the first time `resyncLocalAhead` or `resyncDirtyTracked` prints
   non-zero.
d. THE EVIDENCE ARTIFACT. Not opened in this seat; the resident opens the
   landed copy (section 6, item 5).

<!--RULING spawn=2026-09-07T20:41:08Z-->
