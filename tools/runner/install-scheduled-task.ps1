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
function Get-SupervisorProcesses {
    # MATCHES BOTH DOORS, NOT ONLY THE NEW ONE (B3, found on review). Every
    # supervisor running on this PC TODAY was started by the pre-batch
    # "START EVERYTHING.bat" or the Startup hook, and both of those run
    # tools\supervise.py DIRECTLY - they hold no lock at all, because the
    # lock did not exist before this change. A check that only recognised
    # launch-supervisor.py would count zero here, start the task on top of
    # one of those, and end with two watchers sharing one git index, the
    # exact fight tools/supervise.py's own docstring says cost this project
    # four days. Each match also carries WHICH pattern it was, so a refusal
    # can say which kind of process is already running.
    @(Get-CimInstance Win32_Process `
        -Filter "Name='python.exe' OR Name='pythonw.exe'" `
        -ErrorAction SilentlyContinue |
      Where-Object { $_.CommandLine -and
                     ($_.CommandLine -match 'supervise\.py' -or
                      $_.CommandLine -match 'launch-supervisor\.py') } |
      ForEach-Object {
        $kind = if ($_.CommandLine -match 'launch-supervisor\.py') {
            'launch-supervisor.py'
        } else {
            'supervise.py-direct-no-lock'
        }
        [pscustomobject]@{
            ProcessId = $_.ProcessId
            ParentProcessId = $_.ParentProcessId
            Kind = $kind
        }
      })
}

$Before = Get-SupervisorProcesses
Write-Host "supervisorProcessesBefore=$($Before.Count)"
foreach ($p in $Before) {
    Write-Host "supervisorBeforePid=$($p.ProcessId) supervisorBeforeKind=$($p.Kind)"
}
if ($Before.Count -eq 0) {
    try {
        Start-ScheduledTask -TaskName $TaskName
        Write-Host "startedNow=attempted"
    } catch {
        Write-Host ("startedNow=failed reason=" +
                   ($_.Exception.Message -replace '\s+', ' '))
    }
} else {
    # REFUSE TO START ON TOP OF ONE THAT IS ALREADY RUNNING (B3). Most
    # likely a supervise.py-direct process holding no lock, started before
    # this task existed: starting the task now would run a SECOND
    # supervisor beside it immediately, sharing one git index. The task
    # stays registered either way and takes over cleanly the next time
    # nothing is already running and a fresh logon fires it.
    $kinds = ($Before | ForEach-Object { $_.Kind }) -join ','
    Write-Host ("startedNow=refused reason=" +
               "$($Before.Count)_supervisor_process(es)_already_running " +
               "kinds=$kinds")
}

Start-Sleep -Seconds 3

# VERIFY THE EFFECT, NOT THE EXIT CODE (rule 4). Read the task back from
# Windows rather than trusting the branch that just registered it.
$Task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
$Info = $null
if ($Task) {
    $Info = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction SilentlyContinue
}
$After = Get-SupervisorProcesses

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
Write-Host "supervisorProcessesAfter=$($After.Count)"
foreach ($p in $After) {
    Write-Host ("supervisorPid=$($p.ProcessId) " +
               "supervisorParentPid=$($p.ParentProcessId) " +
               "supervisorKind=$($p.Kind)")
}

if (-not $Task) {
    Write-Host "VERIFY FAILED: the task does not exist after installAction=$InstallAction"
    exit 1
}
Write-Host ("install-scheduled-task: installAction=$InstallAction " +
           "taskExists=True supervisorProcessesAfter=$($After.Count)")
exit 0
