<#
.SYNOPSIS
  Registers the LEDGER supervisor as a Windows scheduled task, ruling
  2026-09-07: "the bot must not depend on a window staying open."

.DESCRIPTION
  Runs tools/runner/launch-supervisor.py - never tools/supervise.py
  directly - at logon for Jafar, and asks Windows to restart it if it
  exits with a failure. launch-supervisor.py is what makes this safe to
  install alongside the two things that already start a supervisor
  (tools/supervise.py's own Startup-folder entry, and a manual
  double-click of "START EVERYTHING.bat"): all three now go through one
  lock, so at most one supervisor is ever actually running, and the
  others print why they stood down rather than fighting over the git
  index the way two unrelated processes would.

  IDEMPOTENT. Reads the task back before writing anything: an identical
  task already registered is left exactly alone and this prints
  installAction=already-correct; a missing or different task is written
  and this prints installAction=create or installAction=update. Running
  this twice never produces two tasks and never starts a second
  supervisor - the lock file answers that question, not this script.

  VERIFIES THE EFFECT, NOT THE EXIT CODE, per rule 4:
  `schtasks /create` (and this module's own Register-ScheduledTask call)
  reporting success is not evidence a task will ever fire. Every write
  is followed by a fresh Get-ScheduledTask / Get-ScheduledTaskInfo read,
  and by asking Windows directly whether a supervisor process is
  running right now.

  NEVER READS tools\runner\config.local. It asks whether the file
  exists with Test-Path and prints only that boolean - the same rule
  tools/supervise.py keeps about the same file.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\runner\install-scheduled-task.ps1
#>
[CmdletBinding()]
param(
    [string]$TaskName = "LEDGER supervisor",
    [string]$TargetUser = "Jafar"
)

$ErrorActionPreference = "Stop"

# THE THREE-WAY PROCESS READ, ONE IMPLEMENTATION. Get-MatchingProcesses
# (query-failed / found-none / found-N, never folding the first into the
# second) is defined once in tools/runner/process-query.ps1 and dot-sourced
# here rather than duplicated, exactly as tools/runner/restart-telegram-
# bot.ps1 also does - one idea in two files is how bootstrap-paths.cmd
# drifted the first time it was copied instead of shared.
. (Join-Path $PSScriptRoot "process-query.ps1")

function Get-SupervisorProcesses {
    # THE THREE KINDS THAT CAN BE HOLDING THIS GIT INDEX (B1, found on
    # review). launch-supervisor.py and a direct supervise.py were the two
    # doors B3 already named; the THIRD is tools\pc-watcher.py, which is
    # what actually hard-resets this checkout every pass
    # (tools/pc-watcher.py:resync). It can be alive with NO supervisor
    # above it at all: supervise.py Popens its children with no job object
    # and only its KeyboardInterrupt path terminates them, a path a
    # windowless, closed-window supervisor never takes - so an orphaned
    # watcher outlives its parent, a check that only knew about the other
    # two would read 0, and the installer would write into an index
    # something else resets once a minute while the evidence says the gate
    # held.
    #
    # THE QUERY ITSELF IS Get-MatchingProcesses; THIS FUNCTION ONLY ADDS
    # THE KIND LABEL each match gets, from the same CommandLine the shared
    # query already read - a caller-side detail the generic query has no
    # reason to know about.
    $r = Get-MatchingProcesses -Pattern ('pc-watcher\.py|supervise\.py|' +
                                        'launch-supervisor\.py')
    if (-not $r.Ok) {
        return [pscustomobject]@{ Ok = $false; Processes = @()
                                  QueryError = $r.QueryError }
    }
    $procs = @($r.Processes | ForEach-Object {
        $kind = if ($_.CommandLine -match 'launch-supervisor\.py') {
            'launch-supervisor.py'
        } elseif ($_.CommandLine -match 'pc-watcher\.py') {
            'pc-watcher.py'
        } else {
            'supervise.py'
        }
        [pscustomobject]@{
            ProcessId = $_.ProcessId
            ParentProcessId = $_.ParentProcessId
            Kind = $kind
        }
      })
    return [pscustomobject]@{ Ok = $true; Processes = $procs; QueryError = "" }
}

function Test-AnySupervisorRunning {
    # ONE READING, USED WHEREVER THIS QUESTION IS ASKED (before the resync,
    # before starting the task, and after, to verify the effect), so the
    # three-way distinction from B1 is reported the same way every time
    # rather than reimplemented at each call site. $Label says which call
    # this was so the evidence file can tell them apart.
    param([string]$Label)
    $r = Get-SupervisorProcesses
    if (-not $r.Ok) {
        Write-Host ("supervisorQueryOk=false supervisorQueryContext=$Label " +
                   "supervisorQueryError=$($r.QueryError)")
        return [pscustomobject]@{ Determined = $false; AnyRunning = $false
                                  Processes = @() }
    }
    Write-Host ("supervisorQueryOk=true supervisorQueryContext=$Label " +
               "supervisorProcessesFound=$($r.Processes.Count)")
    foreach ($p in $r.Processes) {
        Write-Host ("supervisorQueryContext=$Label supervisorPid=$($p.ProcessId) " +
                   "supervisorParentPid=$($p.ParentProcessId) " +
                   "supervisorKind=$($p.Kind)")
    }
    return [pscustomobject]@{ Determined = $true
                              AnyRunning = ($r.Processes.Count -gt 0)
                              Processes = $r.Processes }
}

# THE DEADLOCK, FOUND ON REVIEW: C:\Users\$TargetUser\wc26-picks is stale
# because the only thing that updates it is pc-watcher's resync, which
# runs INSIDE the supervisor, and the supervisor has been down since the
# outage this ruling exists to end. So the install that would keep the
# supervisor alive could not run until something updated the checkout, and
# nothing updated the checkout until the supervisor ran. Broken here, from
# CI, the one thing on this machine that is definitely alive: fetch and
# hard reset BEFORE Find-Repo looks for anything, the same discipline
# tools/supervise.py:resync_once already uses (a discard, not a merge, so
# untracked files - his inbox messages, the packaged build - survive).
#
# THE HAZARD DECIDES WHERE THIS GOES. Two writers on one git index is the
# fight that cost this project four days, so this must never touch the
# checkout while a supervisor OR a bare pc-watcher.py is running: either
# one already keeps this checkout current, and Test-AnySupervisorRunning
# is the same B1/B3 gate reused rather than a second implementation of the
# same question.
#
# THE BRANCH IS A LITERAL, NEVER $env:GITHUB_REF_NAME (B2, found on
# review). This run's push ref happens to equal the daemons' own work
# branch, but the workflow's header plans a future dispatch from `main`,
# and a hard reset onto main's tip would move Jafar's local working-branch
# checkout out from under every daemon reading it. The same string
# tools/runner/inbox.py:WORK_BRANCH, tools/pc-watcher.py:BRANCH and
# tools/supervise.py:run's own fallback already carry is used here
# instead, hard-coded, and the ref this workflow actually ran on is only
# PRINTED, for a mismatch to be visible, never acted on.
$DaemonsBranch = "claude/game-dev-ai-automation-2h67ix"
Write-Host ("workflowRef=$($env:GITHUB_REF_NAME) daemonsBranch=$DaemonsBranch " +
           "daemonsBranchIsWhatGitActuallyUses=true")

$StableForResync = "C:\Users\$TargetUser\wc26-picks"
$ResyncCheck = Test-AnySupervisorRunning -Label "before-resync"

if (-not $ResyncCheck.Determined) {
    Write-Host ("resyncAction=skipped-supervisor-query-failed reason=" +
               "cannot-prove-nothing-is-running-so-refusing-to-touch-" +
               "the-checkout")
} elseif ($ResyncCheck.AnyRunning) {
    $kinds = ($ResyncCheck.Processes | ForEach-Object { $_.Kind }) -join ','
    Write-Host ("resyncAction=skipped-supervisor-running kinds=$kinds " +
               "reason=a-running-supervisor-or-watcher-already-keeps-this-" +
               "checkout-current-do-not-touch-its-index")
} elseif ($env:USERNAME -ne $TargetUser) {
    # THE ACCOUNT CHECK, THE SECOND HALF OF B2. CI writing into
    # $TargetUser's home directory is acceptable only because THIS run's
    # own evidence names the runner account as $TargetUser; an earlier or
    # later era could run this installer as a different (service) account,
    # and that must refuse rather than reset a checkout it does not own.
    Write-Host ("resyncAction=skipped-account-mismatch runnerUser=" +
               "$($env:USERNAME) targetUser=$TargetUser reason=refusing-" +
               "to-write-into-a-different-accounts-home-directory")
} elseif (-not (Test-Path (Join-Path $StableForResync ".git"))) {
    Write-Host ("resyncAction=skipped-no-git-checkout-there path=" +
               "$($StableForResync -replace ' ','~')")
} else {
    # SAFE.DIRECTORY, THE SAME WAY THE WORKFLOW'S OWN GIT STEPS ALREADY SET
    # IT, rather than inventing a second approach: a self-hosted runner
    # account touching a directory owned by $TargetUser is exactly the
    # shape git's dubious-ownership guard exists for.
    $env:GIT_CONFIG_COUNT = "1"
    $env:GIT_CONFIG_KEY_0 = "safe.directory"
    $env:GIT_CONFIG_VALUE_0 = "*"
    $env:GIT_EDITOR = "true"
    $env:GIT_MERGE_AUTOEDIT = "no"
    $env:GIT_TERMINAL_PROMPT = "0"
    Push-Location $StableForResync
    try {
        # A1, THE EVIDENCE OWED BEFORE A DESTRUCTIVE OPERATION. A hard
        # reset discards local commits, and production/inbox, outbox and
        # outbound ARE TRACKED on this branch (321 files, measured by
        # `git ls-tree`) while the PC's own writers treat their copies as
        # untracked; game-design/pc-jobs/result.txt is tracked too, and
        # the watcher writes it. The reflog keeps what a reset discards,
        # but only if this evidence names the sha to recover FROM.
        $HeadSha = (& git rev-parse HEAD 2>&1)
        Write-Host "resyncLocalAhead=$HeadSha"
        $StatusLines = @(& git status --porcelain=v1 2>&1)
        $DirtyTracked = @($StatusLines | Where-Object { $_ -notmatch '^\?\?' })
        Write-Host "resyncDirtyTrackedPaths=$($DirtyTracked.Count)"
        foreach ($line in $DirtyTracked) {
            Write-Host "resyncDirtyTracked=$($line.Trim() -replace '\s+','_')"
        }

        # STDERR IS CAPTURED, NEVER DISCARDED (A1). A failure used to leave
        # exitCode=128 with no words in the only channel anyone can read;
        # a stale .git/index.lock from the 11:30 stop is one of the named
        # ways this can fail, and its message only exists on stderr.
        $FetchOutput = (& git fetch origin $DaemonsBranch 2>&1 |
                        ForEach-Object { $_.ToString() })
        $fetchExit = $LASTEXITCODE
        if ($fetchExit -ne 0) {
            Write-Host ("resyncAction=failed-fetch branch=$DaemonsBranch " +
                       "exitCode=$fetchExit error=$($FetchOutput -join ' | ')")
        } else {
            $sha = (& git rev-parse FETCH_HEAD 2>&1)
            if (-not $sha -or $sha -match '^fatal:') {
                Write-Host ("resyncAction=failed-no-fetch-head " +
                           "branch=$DaemonsBranch error=$sha")
            } else {
                $ResetOutput = (& git reset --hard $sha 2>&1 |
                                ForEach-Object { $_.ToString() })
                $resetExit = $LASTEXITCODE
                if ($resetExit -ne 0) {
                    Write-Host ("resyncAction=failed-reset " +
                               "branch=$DaemonsBranch sha=$sha " +
                               "exitCode=$resetExit " +
                               "error=$($ResetOutput -join ' | ')")
                } else {
                    $short = $sha.Substring(0, [Math]::Min(7, $sha.Length))
                    Write-Host ("resyncAction=updated branch=$DaemonsBranch " +
                               "sha=$short")
                }
            }
        }
    } finally {
        Pop-Location
    }
}

function Find-Repo {
    # THE STABLE PATH FIRST, ALWAYS (B5, found on review). Not
    # $env:USERPROFILE: under the self-hosted runner SERVICE, USERPROFILE
    # is whichever account runs that service, not necessarily
    # $TargetUser, and this project's own probe workflow already
    # hard-codes exactly this path (C:\Users\Jafar\wc26-picks by default)
    # as the one checkout that survives between jobs. Everything else on
    # this machine under a service-era runner - including wherever THIS
    # SCRIPT itself happens to be checked out - can be the runner's own
    # `_work` directory, which gets swept between runs.
    $stable = "C:\Users\$TargetUser\wc26-picks"
    $runnerAccount = "$env:COMPUTERNAME\$env:USERNAME"
    Write-Host "runnerAccount=$runnerAccount"
    if (Test-Path (Join-Path $stable "CLAUDE.md")) {
        return (Resolve-Path $stable).Path
    }
    if ($env:GITHUB_ACTIONS -eq "true") {
        # REFUSE RATHER THAN GUESS. The only other candidate visible here
        # is wherever actions/checkout put THIS run's own checkout, which
        # the runner sweeps between jobs - registering a scheduled task
        # pointed at that path would have it running from a directory that
        # stops existing the moment the next job starts, exactly the fault
        # named on review.
        throw ("COULD NOT FIND THE STABLE PROJECT CHECKOUT at " +
              "`"$stable`" while running under GitHub Actions as " +
              "$runnerAccount. Refusing to fall back to this run's own " +
              "(swept) checkout directory. Nothing was registered. Clone " +
              "the project to $stable once by hand, or dispatch again " +
              "after it exists there.")
    }
    # NOT CI: the same two-step search "START EVERYTHING.bat" makes, kept
    # for the case Jafar runs this file directly, possibly from a copy.
    $named = Join-Path $env:USERPROFILE "wc26-picks"
    if (Test-Path (Join-Path $named "CLAUDE.md")) {
        return (Resolve-Path $named).Path
    }
    $here = Split-Path -Parent $PSCommandPath
    $fromScript = Split-Path -Parent (Split-Path -Parent $here)
    if (Test-Path (Join-Path $fromScript "CLAUDE.md")) {
        return (Resolve-Path $fromScript).Path
    }
    throw ("COULD NOT FIND THE PROJECT. Looked in `"$stable`", " +
          "`"$named`" and `"$fromScript`" (ran as $runnerAccount). " +
          "Nothing was registered.")
}

function Find-Python {
    param([string]$Repo)
    # SAME ORDER AS "START EVERYTHING.bat": the voice environment first
    # (only the watcher needs it, but any 3.8+ interpreter can run the
    # supervisor itself), then miniconda, then whatever `python.exe` or
    # `py -3` resolves on PATH.
    $tries = @(
        (Join-Path $Repo "tools\voice-live\env-export\Scripts\python.exe"),
        (Join-Path $env:USERPROFILE "miniconda3\python.exe")
    )
    foreach ($t in $tries) {
        if (Test-Path $t) { return $t }
    }
    $onPath = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($onPath) { return $onPath.Source }
    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($py) { return $py.Source }
    throw ("NO PYTHON 3.8+ FOUND on this machine, in any of the places " +
          "START EVERYTHING.bat also checks. Nothing was registered.")
}

function Find-Windowless {
    # A CONSOLE WINDOW IS THE ONE THING THIS TASK MUST NEVER OPEN - the
    # whole point is that nobody has to be watching one. Task Scheduler's
    # own "Hidden" setting hides the TASK from its own UI list; it does
    # not hide a console window the action opens, so the actual answer is
    # to launch pythonw.exe, which never allocates a console at all, when
    # one sits beside the interpreter Find-Python found.
    param([string]$PythonPath)
    $candidate = Join-Path (Split-Path -Parent $PythonPath) "pythonw.exe"
    if (Test-Path $candidate) { return $candidate }
    return $PythonPath
}

$Repo = Find-Repo
$Python = Find-Python -Repo $Repo
$PythonW = Find-Windowless -PythonPath $Python
$Launcher = Join-Path $Repo "tools\runner\launch-supervisor.py"
if (-not (Test-Path $Launcher)) {
    throw ("MISSING $Launcher - the door every launch is meant to go " +
          "through is not on disk. Nothing was registered.")
}

Write-Host "repo=$($Repo -replace ' ','~')"
Write-Host "python=$($Python -replace ' ','~')"
Write-Host "pythonForTask=$($PythonW -replace ' ','~') windowless=$($PythonW -ne $Python)"

# CONFIG.LOCAL: EXISTENCE ONLY. This line is the entire relationship this
# script has with that file - it is never opened, so nothing inside it can
# ever reach this output or anything committed from it.
$ConfigPresent = Test-Path (Join-Path $Repo "tools\runner\config.local")
Write-Host "configLocalPresent=$ConfigPresent"

$TaskArgs = "`"$Launcher`" scheduled-task"
$DesiredAction = New-ScheduledTaskAction -Execute $PythonW -Argument $TaskArgs `
    -WorkingDirectory $Repo
$DesiredTrigger = New-ScheduledTaskTrigger -AtLogOn -User $TargetUser
$DesiredSettings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -Hidden
$DesiredPrincipal = New-ScheduledTaskPrincipal -UserId $TargetUser `
    -LogonType Interactive -RunLevel Limited
$Description = ("LEDGER: keeps studio-watcher, telegram-bot and " +
                "claude-executor running without a window open, through " +
                "tools/runner/launch-supervisor.py so a second launch " +
                "cannot start a second supervisor. Installed by " +
                "tools/runner/install-scheduled-task.ps1, ruling " +
                "2026-09-07. Manual fallback: START EVERYTHING.bat.")

function Test-TaskMatches {
    param($Task)
    if (-not $Task) { return $false }
    $a = $Task.Actions | Select-Object -First 1
    if (-not $a) { return $false }
    $execOk = ($a.Execute -eq $PythonW)
    $argOk = ($a.Arguments -eq $TaskArgs)
    $wdOk = ($a.WorkingDirectory -eq $Repo)
    $trig = $Task.Triggers | Select-Object -First 1
    $trigOk = ($trig -and $trig.CimClass.CimClassName -match 'LogonTrigger')
    $s = $Task.Settings
    $setOk = ($s.MultipleInstances -eq 'IgnoreNew') -and
             ($s.RestartCount -eq 999) -and ($s.Hidden -eq $true)
    return ($execOk -and $argOk -and $wdOk -and $trigOk -and $setOk)
}

$Existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
$InstallAction = "none"
try {
    if (-not $Existing) {
        Register-ScheduledTask -TaskName $TaskName -Action $DesiredAction `
            -Trigger $DesiredTrigger -Settings $DesiredSettings `
            -Principal $DesiredPrincipal -Description $Description | Out-Null
        $InstallAction = "create"
    } elseif (-not (Test-TaskMatches $Existing)) {
        Register-ScheduledTask -TaskName $TaskName -Action $DesiredAction `
            -Trigger $DesiredTrigger -Settings $DesiredSettings `
            -Principal $DesiredPrincipal -Description $Description `
            -Force | Out-Null
        $InstallAction = "update"
    } else {
        $InstallAction = "already-correct"
    }
} catch {
    Write-Host ("installActionFailed=true installActionError=" +
               ($_.Exception.Message -replace '\s+', ' '))
    Write-Host "installAction=failed"
    exit 1
}
Write-Host "installAction=$InstallAction"

# START IT NOW IF NOTHING IS RUNNING, rather than only at the next logon:
# the point of running this while he is away is that it is alive before
# he is back. A failed attempt here is not fatal - it commonly means no
# interactive session for $TargetUser exists on this machine right now -
# and the AtLogOn trigger still fires correctly the next time it does.
# Test-AnySupervisorRunning is defined once, near the top of this file,
# and reused here rather than redefined: it is the same B1/B3 question
# asked again after the resync and the install, not a second
# implementation.
$StartCheck = Test-AnySupervisorRunning -Label "before-start"
if (-not $StartCheck.Determined) {
    # A QUERY THAT FAILED MUST REFUSE, NOT ASSUME NOTHING IS RUNNING (B1).
    # The task stays registered and fires normally at the next logon.
    Write-Host ("startedNow=refused reason=supervisor-query-failed-cannot-" +
               "prove-nothing-is-running")
} elseif (-not $StartCheck.AnyRunning) {
    try {
        Start-ScheduledTask -TaskName $TaskName
        Write-Host "startedNow=attempted"
    } catch {
        Write-Host ("startedNow=failed reason=" +
                   ($_.Exception.Message -replace '\s+', ' '))
    }
} else {
    # REFUSE TO START ON TOP OF ONE THAT IS ALREADY RUNNING (B3, and B1's
    # third kind). Starting the task now would run a SECOND supervisor (or
    # a supervisor beside an orphaned watcher) immediately, sharing one
    # git index. The task stays registered either way and takes over
    # cleanly the next time nothing is already running and a fresh logon
    # fires it.
    $kinds = ($StartCheck.Processes | ForEach-Object { $_.Kind }) -join ','
    Write-Host ("startedNow=refused reason=" +
               "$($StartCheck.Processes.Count)_supervisor_process(es)_" +
               "already_running kinds=$kinds")
}

Start-Sleep -Seconds 3

# VERIFY THE EFFECT, NOT THE EXIT CODE (rule 4). Read the task back from
# Windows rather than trusting the branch that just registered it.
$Task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
$Info = $null
if ($Task) {
    $Info = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction SilentlyContinue
}
$AfterCheck = Test-AnySupervisorRunning -Label "after-verify"

Write-Host "taskExists=$([bool]$Task)"
if ($Task) {
    Write-Host "taskState=$($Task.State)"
    Write-Host "taskEnabled=$($Task.Settings.Enabled)"
    $trig = $Task.Triggers | Select-Object -First 1
    $trigKind = if ($trig) { $trig.CimClass.CimClassName } else { "none" }
    Write-Host "taskTriggerKind=$trigKind"
    Write-Host "taskRestartCount=$($Task.Settings.RestartCount)"
    Write-Host "taskRestartInterval=$($Task.Settings.RestartInterval)"
    Write-Host "taskMultipleInstancesPolicy=$($Task.Settings.MultipleInstances)"
    Write-Host "taskHiddenInSchedulerUI=$($Task.Settings.Hidden)"
    Write-Host "taskRunAsUser=$($Task.Principal.UserId)"
    Write-Host "taskLogonType=$($Task.Principal.LogonType)"
}
if ($Info) {
    Write-Host "taskLastRunTime=$($Info.LastRunTime)"
    Write-Host "taskLastTaskResult=$($Info.LastTaskResult)"
    Write-Host "taskNextRunTime=$($Info.NextRunTime)"
}
# Test-AnySupervisorRunning already printed supervisorQueryOk,
# supervisorProcessesFound and one line per match above, tagged
# supervisorQueryContext=after-verify - not repeated here, so one query is
# one set of lines rather than two.

if (-not $Task) {
    Write-Host "VERIFY FAILED: the task does not exist after installAction=$InstallAction"
    exit 1
}
$AfterCount = if ($AfterCheck.Determined) { "$($AfterCheck.Processes.Count)" }
              else { "unknown-query-failed" }
Write-Host ("install-scheduled-task: installAction=$InstallAction " +
           "taskExists=True supervisorProcessesAfter=$AfterCount")
exit 0
