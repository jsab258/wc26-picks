<#
.SYNOPSIS
  Route b, ruling 2026-09-07 section 5 item 3b, AMENDED by the ruling
  "the remote restart job, and the pair of processes it would have
  refused" after the first version refused on its own accepting case.
  Stops the telegram-bot.py PROCESS TREE (a venv redirector plus the base
  interpreter it launches as a child, bpo-34977) so tools\supervise.py
  restarts it from the code already on disk, without paging Jafar to the
  floor at midnight for something the studio can do.

.DESCRIPTION
  WHY A TREE AND NOT A PID. Every daemon this project spawns through
  sys.executable inside a venv is TWO python.exe processes on Windows: a
  redirector that launches the base interpreter as a child and waits for
  it, and the interpreter itself. Landed evidence shows this on his
  machine for both supervise.py and pc-watcher.py, so the telegram-bot.py
  pattern matches two processes on the accepting case, not one. A plain
  count-of-1 gate refuses every real run; a plain "stop everything that
  matched" kills the wrong one first (Stop-Process does not cascade -
  stopping the redirector orphans the still-running interpreter while the
  supervisor spawns a second one on the same Telegram token). So the
  match is read as a TREE: exactly one ROOT (a matched process whose
  parent is not itself in the matched set) and zero or more LEAVES (the
  rest). The interpreter is the leaf; the redirector is the root, because
  its own parent is outside the bot's matched set. Leaves are stopped
  first; the root is given a few seconds to exit on its own (which it
  does, once its child is gone) before being stopped itself.

  THE ROOT'S PARENT MUST BE A RUNNING SUPERVISOR. A bot started by hand
  (for example the older "START THE TELEGRAM BOT.bat") has nothing above
  it, and stopping it would leave Jafar with no channel and nothing that
  will bring one back. So the root's ParentProcessId must itself be a
  member of the set matched by `supervise\.py|launch-supervisor\.py`
  (unanchored: this only asks whether a supervisor process exists there,
  not which half of a redirector pair it is), or this refuses.

  THE WAIT IS MEASURED, NOT A CONSTANT. tools/supervise.py's loop ticks
  once a second and can notice an exit up to one tick late, so a
  respawned process can appear five to about seven seconds after the
  kill; a single check at a fixed 5 seconds is a coin flip. This polls
  once a second for up to $ComeBackCeilingSec seconds and reports
  `botCameBackAfterSec=<N>` (the real number, not a guess), telling a new
  process apart from a REUSED PID by CreationDate rather than by PID.
  Then it waits a further $StabilitySec seconds and re-queries: the SAME
  tree still present is the actual verdict, because a process that comes
  back and then dies is the crash loop tools/supervise.py's give-up rule
  exists for (five stops in thirty minutes), not a restart. One
  deliberate stop tonight is nowhere near that rule; a NEW respawn dying
  from an import or startup fault is the one thing that could approach
  it, and that is exactly what the stability wait is checking for.

  WHAT PROVES THE NEW PROCESS RAN TODAY'S CODE. Nothing the bot prints at
  startup names its own code version, so the strongest evidence available
  tonight is read from the checkout the supervisor loads from, at
  $TargetUser's stable path, before the stop and again after the return:
  the checkout's own HEAD (`stableHead`, via `git rev-parse`, read-only,
  takes no lock) and the SHA-256 of tools/runner/telegram-bot.py and
  tools/runner/outbox.py there. None of this proves a clip can be sent;
  only a `receipt: sent-with-clip` on pc-inbox proves that, and this
  script makes no claim otherwise.

  DISTINCT EXIT CODES (added on review): 0 restarted and stable; 2
  refused, nothing on his machine was touched; 1 a stop was attempted and
  the outcome could not be confirmed. `botStopped=true` or `=false` is
  printed on every single path, so a reader never has to infer whether
  his machine was changed from the absence of another line.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\runner\restart-telegram-bot.ps1
#>
[CmdletBinding()]
param(
    [string]$TargetUser = "Jafar",
    [int]$ComeBackCeilingSec = 30,
    [int]$StabilitySec = 20,
    [int]$RootExitGraceSec = 3
)

$ErrorActionPreference = "Stop"

# THE SAME THREE-WAY READ, NOT A SECOND ONE. Defined once in
# tools/runner/process-query.ps1 and dot-sourced here exactly as
# tools/runner/install-scheduled-task.ps1 now does.
. (Join-Path $PSScriptRoot "process-query.ps1")

# EXIT CODES, NAMED (A2, found on review). All refusals and all failures
# used to share exit 1, so the workflow's own exit code could not tell
# "nothing was touched" from "his bot was stopped and never seen again".
$EXIT_OK = 0
$EXIT_REFUSED = 2
$EXIT_FAILURE = 1

# ANCHORED AT THE END OF THE COMMAND LINE (found on review, section 1).
# Unanchored, `tools\\runner\\telegram-bot\.py` also matches
# `telegram-bot.py --selftest`, a copy in an executor worktree, or a copy
# under a swept `_work` checkout - all real strings that can appear on
# this machine. The supervisor's own spawn (tools/supervise.py 602 to
# 603) is the interpreter and the script path and NOTHING after it, so
# the end of the command line is a discriminator that costs nothing.
$BotPattern = 'tools\\runner\\telegram-bot\.py"?\s*$'

# UNANCHORED ON PURPOSE. This only asks whether a supervisor process
# exists at all; it does not care which half of a redirector pair it is,
# since both halves of that pair carry the identical command line.
$SupervisorPattern = 'supervise\.py|launch-supervisor\.py'

function ConvertTo-Printable {
    param([string]$Text)
    if (-not $Text) { return "none" }
    return ($Text -replace ' ', '~')
}

function Write-BotCandidates {
    param($Procs, [string]$Prefix)
    foreach ($p in $Procs) {
        Write-Host ("$Prefix" + "Pid=$($p.ProcessId) " + "$Prefix" +
                   "ParentPid=$($p.ParentProcessId) " + "$Prefix" +
                   "CommandLine=$(ConvertTo-Printable $p.CommandLine)")
    }
}

function Get-ProcessTree {
    # THE MATCH AS A TREE, NOT A COUNT (found on review, section 1). A
    # root is a matched process whose parent is NOT itself in the matched
    # set; refuses unless there is exactly one. Everything else in the
    # set is a leaf. Two roots (or zero, which cannot happen given at
    # least one match, since some member's parent chain must terminate
    # inside the set or outside it) means something this script does not
    # understand is running and it must not guess which one to stop.
    param($Procs)
    $ids = @($Procs | ForEach-Object { $_.ProcessId })
    $roots = @($Procs | Where-Object { $ids -notcontains $_.ParentProcessId })
    if ($roots.Count -ne 1) {
        return [pscustomobject]@{
            Ok = $false
            Reason = "found-$($roots.Count)-root(s)-in-$($Procs.Count)-matched-process(es)"
            Root = $null; Leaves = @()
        }
    }
    $root = $roots[0]
    $leaves = @($Procs | Where-Object { $_.ProcessId -ne $root.ProcessId })
    return [pscustomobject]@{ Ok = $true; Reason = ""; Root = $root; Leaves = $leaves }
}

function Get-BotTree {
    # One query, one tree, used identically before the stop, while
    # polling for the comeback, and for the stability check - one
    # implementation of "what does the current match look like" rather
    # than three.
    $r = Get-MatchingProcesses -Pattern $BotPattern
    if (-not $r.Ok) {
        return [pscustomobject]@{ QueryOk = $false; QueryError = $r.QueryError
                                  Tree = $null; Count = 0; Processes = @() }
    }
    $tree = if ($r.Processes.Count -gt 0) { Get-ProcessTree -Procs $r.Processes } else { $null }
    return [pscustomobject]@{ QueryOk = $true; QueryError = ""
                              Tree = $tree; Count = $r.Processes.Count
                              Processes = $r.Processes }
}

$RunnerAccount = "$env:COMPUTERNAME\$env:USERNAME"
Write-Host "runnerAccount=$RunnerAccount"
Write-Host "targetUser=$TargetUser"

if ($env:USERNAME -ne $TargetUser) {
    Write-Host ("restartAction=refused-account-mismatch runnerUser=" +
               "$($env:USERNAME) targetUser=$TargetUser")
    Write-Host "botStopped=false"
    exit $EXIT_REFUSED
}

# A3, FOUND ON REVIEW: THE EVIDENCE THAT THE DISK HELD TODAY'S CODE,
# PRINTED BEFORE ANYTHING IS TOUCHED. Read-only: `rev-parse` takes no
# lock, so this is not a second writer on the watcher's own index.
$StablePath = "C:\Users\$TargetUser\wc26-picks"
function Write-StableEvidence {
    # THE KEYS ARE THE ONES THE RULING NAMES, UNSUFFIXED, printed twice
    # (before the stop, after the return): stableHead=, botSourceSha256=,
    # outboxSourceSha256=. $When is its own marker line rather than a
    # suffix on the key, so a reader comparing the two greps for the
    # identical key sees the identical name the ruling wrote.
    param([string]$When)
    Write-Host "stableEvidence=$When"
    $head = "unknown"
    try {
        $out = (& git -c safe.directory=* -C $StablePath rev-parse HEAD 2>&1)
        if ($LASTEXITCODE -eq 0 -and $out) { $head = $out.ToString().Trim() }
    } catch { $head = "unknown" }
    Write-Host "stableHead=$head"
    foreach ($rel in @("tools\runner\telegram-bot.py", "tools\runner\outbox.py")) {
        $full = Join-Path $StablePath $rel
        $key = if ($rel -match 'telegram-bot') { "botSourceSha256" } else { "outboxSourceSha256" }
        if (Test-Path $full) {
            Write-Host "$key=$((Get-FileHash -Path $full -Algorithm SHA256).Hash)"
        } else {
            Write-Host "$key=file-not-found path=$(ConvertTo-Printable $full)"
        }
    }
}
Write-StableEvidence -When "before"

$Before = Get-BotTree
if (-not $Before.QueryOk) {
    Write-Host "botQueryOk=false botQueryError=$($Before.QueryError)"
    Write-Host ("restartAction=refused-query-failed reason=cannot-prove-" +
               "how-many-bot-processes-are-running")
    Write-Host "botStopped=false"
    exit $EXIT_REFUSED
}
Write-Host "botQueryOk=true botProcessesFound=$($Before.Count)"

if ($Before.Count -eq 0) {
    Write-Host ("restartAction=refused-none-found reason=the-bot-may-be-" +
               "mid-restart-or-given-up-on;killing-nothing-while-" +
               "reporting-success-is-the-fault-this-exists-to-end")
    Write-Host "botStopped=false"
    exit $EXIT_REFUSED
}

Write-BotCandidates -Procs $Before.Processes -Prefix "botCandidate"

if (-not $Before.Tree.Ok) {
    Write-Host "botTreeBefore=refused-$($Before.Tree.Reason)"
    Write-Host ("restartAction=refused-more-than-one reason=" +
               "$($Before.Tree.Reason);something-else-is-already-wrong;" +
               "stopping-one-at-random-would-hide-it")
    Write-Host "botStopped=false"
    exit $EXIT_REFUSED
}

$Root = $Before.Tree.Root
$Leaves = $Before.Tree.Leaves
$LeafPids = @($Leaves | ForEach-Object { $_.ProcessId })
Write-Host ("botTreeBefore=$($Root.ParentProcessId)>$($Root.ProcessId)>" +
           "$($LeafPids -join ',')")
Write-Host "botRootCommandLine=$(ConvertTo-Printable $Root.CommandLine)"

# THE PARENT OF THE ROOT MUST BE A RUNNING SUPERVISOR (found on review).
$SupervisorNow = Get-MatchingProcesses -Pattern $SupervisorPattern
$SupervisorPids = if ($SupervisorNow.Ok) {
    @($SupervisorNow.Processes | ForEach-Object { $_.ProcessId })
} else { @() }
Write-Host ("supervisorQueryOk=$($SupervisorNow.Ok) " +
           "supervisorPidsSeen=$($SupervisorPids -join ',')")
if (-not $SupervisorNow.Ok -or ($SupervisorPids -notcontains $Root.ParentProcessId)) {
    Write-Host ("restartAction=refused-no-supervisor-above-it reason=" +
               "the-roots-parent-$($Root.ParentProcessId)-is-not-a-" +
               "running-supervisor;stopping-it-would-leave-no-channel-" +
               "and-nothing-to-bring-one-back")
    Write-Host "botStopped=false"
    exit $EXIT_REFUSED
}

# LEAF FIRST. Stop-Process does not cascade: stopping the root (the
# redirector) first would orphan the still-running leaf while the
# supervisor spawns a second bot on the same token. Stopping the leaf
# first makes the redirector exit on its own with the child's own code,
# which is exactly the exit tools/supervise.py is built to notice. A leaf
# that has already gone is recorded as gone, never as a failure.
$LeafStopFailed = $false
foreach ($leaf in $Leaves) {
    try {
        if (Get-Process -Id $leaf.ProcessId -ErrorAction SilentlyContinue) {
            Stop-Process -Id $leaf.ProcessId -Force
            Write-Host "botLeafStopped=$($leaf.ProcessId)"
        } else {
            Write-Host "botLeafAlreadyGone=$($leaf.ProcessId)"
        }
    } catch {
        Write-Host ("botLeafStopFailed=$($leaf.ProcessId) reason=" +
                   ($_.Exception.Message -replace '\s+', ' '))
        $LeafStopFailed = $true
    }
}
if ($LeafStopFailed) {
    Write-Host ("restartAction=refused-stop-failed reason=" +
               "the-leaf-could-not-be-stopped-so-nothing-was-touched")
    Write-Host "botStopped=false"
    exit $EXIT_REFUSED
}

# THE ROOT GETS A FEW SECONDS TO LEAVE ON ITS OWN, then is stopped only
# if it has not. This is the redirector noticing its child died.
$StopInstant = Get-Date
$RootGone = $false
for ($i = 1; $i -le $RootExitGraceSec; $i++) {
    Start-Sleep -Seconds 1
    if (-not (Get-Process -Id $Root.ProcessId -ErrorAction SilentlyContinue)) {
        $RootGone = $true
        break
    }
}
if ($RootGone) {
    Write-Host "botRootExitedOnItsOwn=true"
} else {
    try {
        Stop-Process -Id $Root.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "botRootStopped=true"
    } catch {
        Write-Host ("botRootStopped=false reason=" +
                   ($_.Exception.Message -replace '\s+', ' '))
    }
}
$BotOldPid = if ($LeafPids.Count -gt 0) { $LeafPids[0] } else { $Root.ProcessId }
Write-Host "botOldPid=$BotOldPid"
Write-Host "botStopInstant=$($StopInstant.ToUniversalTime().ToString('o'))"
# THE DESTRUCTIVE ACT HAS NOW HAPPENED, REGARDLESS OF WHAT FOLLOWS. Every
# line below this point is verification, not the deed, so botStopped is
# already settled.
$BotStopped = $true

# THE COMEBACK IS POLLED, NOT GUESSED (B2, found on review). One check a
# fixed 5 seconds in was a coin flip: the supervisor's loop ticks once a
# second and can notice the exit up to one tick late, so a real respawn
# can land at 5, 6 or 7 seconds. This polls once a second up to
# $ComeBackCeilingSec and records the real number.
$NewTreeInfo = $null
$CameBackAfterSec = $null
for ($sec = 1; $sec -le $ComeBackCeilingSec; $sec++) {
    Start-Sleep -Seconds 1
    $probe = Get-BotTree
    if (-not $probe.QueryOk) { continue }
    if ($probe.Count -gt 0 -and $probe.Tree -and $probe.Tree.Ok) {
        # NEW BY CreationDate, NEVER BY PID. Windows reuses process ids,
        # so a PID that differs from the one just stopped is not proof by
        # itself; a creation time after the stop instant is.
        if ($probe.Tree.Root.CreationDate -and
            $probe.Tree.Root.CreationDate -gt $StopInstant) {
            $NewTreeInfo = $probe
            $CameBackAfterSec = $sec
            break
        }
    }
}
if ($CameBackAfterSec) {
    Write-Host "botCameBackAfterSec=$CameBackAfterSec"
} else {
    Write-Host "botCameBackAfterSec=none waitedSec=$ComeBackCeilingSec"
    Write-Host ("restartAction=stopped-but-did-not-come-back reason=the-" +
               "restart-path-has-never-run-for-real-before-treat-this-" +
               "as-a-genuine-finding")
    Write-Host "botStopped=$BotStopped"
    Write-StableEvidence -When "after"
    exit $EXIT_FAILURE
}

$NewRoot = $NewTreeInfo.Tree.Root
$NewLeafPids = @($NewTreeInfo.Tree.Leaves | ForEach-Object { $_.ProcessId })
$BotNewPid = if ($NewLeafPids.Count -gt 0) { $NewLeafPids[0] } else { $NewRoot.ProcessId }
Write-Host "botNewPid=$BotNewPid"
Write-Host "botPidChanged=$([bool]($BotNewPid -ne $BotOldPid))"
Write-Host "botTreeJustAfter=$($NewRoot.ParentProcessId)>$($NewRoot.ProcessId)>$($NewLeafPids -join ',')"
Write-Host "botRootCreationDate=$($NewRoot.CreationDate)"

# THE STABILITY CHECK IS THE VERDICT, NOT THE COMEBACK (B2). A process
# that appears and then dies from an import or startup fault in today's
# code is the crash loop tools/supervise.py's give-up rule exists for
# (five stops inside thirty minutes); this is the one thing a single
# deliberate stop could plausibly trip if the new code is broken, so it
# is checked for rather than assumed away.
Start-Sleep -Seconds $StabilitySec
$After = Get-BotTree
$Stable = $false
if ($After.QueryOk -and $After.Count -gt 0 -and $After.Tree -and $After.Tree.Ok) {
    $afterRoot = $After.Tree.Root
    $afterLeafPids = @($After.Tree.Leaves | ForEach-Object { $_.ProcessId })
    Write-Host "botTreeAfter=$($afterRoot.ParentProcessId)>$($afterRoot.ProcessId)>$($afterLeafPids -join ',')"
    $sameRoot = ($afterRoot.ProcessId -eq $NewRoot.ProcessId)
    $sameLeaves = (@($afterLeafPids) -join ',') -eq (@($NewLeafPids) -join ',')
    $Stable = [bool]($sameRoot -and $sameLeaves)
} else {
    $reason = if (-not $After.QueryOk) { $After.QueryError } else { "no-matching-tree" }
    Write-Host "botTreeAfter=none reason=$(ConvertTo-Printable $reason)"
}

if ($Stable) {
    Write-Host "botNewTreeStableForSec=$StabilitySec"
} else {
    Write-Host "botNewTreeStableForSec=none"
}
Write-StableEvidence -When "after"
Write-Host "botStopped=$BotStopped"

if (-not $Stable) {
    Write-Host ("restartAction=stopped-but-not-stable reason=the-new-" +
               "process-did-not-survive-$($StabilitySec)s;this-is-the-" +
               "crash-loop-shape-not-a-clean-restart")
    exit $EXIT_FAILURE
}
Write-Host "restartAction=restarted"
exit $EXIT_OK
