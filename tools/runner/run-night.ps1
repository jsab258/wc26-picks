# LEDGER overnight runner. WRITTEN ON THE CONTAINER, EXECUTES ON WINDOWS.
# Untested where written: this container has no PowerShell (the verify
# footer names that lint NOT CHECKED), so the first Windows run is this
# script's accepting test, per rule 5b, and should be watched end to end.
# Authority: ledger-v2/studio-v2/runner.md. Kill switch: production/STOP.
param(
    [int]$MaxIterations = 40,
    [int]$WallClockHours = 9,
    [switch]$Register    # register the nightly Task Scheduler entry and exit
)
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $repo

if ($Register) {
    schtasks /Create /TN "LEDGER-night-runner" /TR "`"$PSScriptRoot\run-night.bat`"" /SC DAILY /ST 23:30 /F
    Write-Host "Registered LEDGER-night-runner, daily 23:30. The STOP file still wins."
    exit 0
}

$night  = "night/" + (Get-Date -Format "yyyyMMdd")
$logdir = Join-Path $repo ("production/logs/night-" + (Get-Date -Format "yyyyMMdd"))
New-Item -ItemType Directory -Force -Path $logdir | Out-Null
git fetch origin
git checkout -B $night origin/claude/game-dev-ai-automation-2h67ix

$deadline = (Get-Date).AddHours($WallClockHours)
$dispatch = Get-Content (Join-Path $PSScriptRoot "dispatch.md") -Raw
$i = 0
while ($true) {
    $i++
    if (Test-Path "production/STOP") { Write-Host "STOP file present; exiting."; break }
    if ($i -gt $MaxIterations)       { Write-Host "Max iterations reached.";     break }
    if ((Get-Date) -gt $deadline)    { Write-Host "Wall clock limit reached.";   break }
    $queued = Get-ChildItem "production/queue" -Filter "*.md" -File |
              Where-Object { $_.Name -ne "README.md" }
    if (-not $queued) { Write-Host "Queue empty."; break }
    $log = Join-Path $logdir ("iter-{0:d3}.log" -f $i)
    Write-Host ("Iteration {0}: {1} task(s) queued. Logging to {2}" -f $i, $queued.Count, $log)
    & claude -p $dispatch --max-turns 200 *> $log
    if ($LASTEXITCODE -ne 0) { Write-Host ("Session exited {0}; see log." -f $LASTEXITCODE) }

    # THE DASHBOARD IS REGENERATED AT THE END OF EVERY ITERATION, so the page
    # describes the night as it happens rather than as it was at 23:30.
    # NEVER FATAL: a night that stops because a status page failed to build
    # would be the instrument breaking the work it measures. It says so
    # instead, and the page then carries the age of its own last rebuild.
    $py = $null
    foreach ($cand in @("python", "python3", "py")) {
        if (Get-Command $cand -ErrorAction SilentlyContinue) { $py = $cand; break }
    }
    if ($py) {
        & $py "tools/dashboard/build-dashboard.py" 2>&1 | Write-Host
        if ($LASTEXITCODE -ne 0) { Write-Host "Dashboard did not rebuild this iteration; STATUS.md is as old as its own header." }
        # STAGE ONLY WHAT IS ALREADY TRACKED. `git add -u -- <paths>` touches
        # tracked files and ignores untracked ones, so whether dashboard.html
        # is committed at all stays a repository decision rather than one this
        # script makes silently at 3am.
        git add -u -- STATUS.md dashboard.html 2>$null
        git diff --cached --quiet
        if ($LASTEXITCODE -ne 0) { git commit -m ("Status dashboard, iteration {0}" -f $i) 2>$null }
    } else {
        Write-Host "No python found; the dashboard was not rebuilt this iteration."
    }
    git push -u origin $night
}

# BRIEF DELIVERY, AND THERE IS ONE WRITER OF A BRIEF IN THIS PROJECT:
# tools/morning-brief.py. Ruled 2026-09-05, section 7(b) of
# game-design/decision-2026-09-05-ruling-standing-order-refill-and-the-wake-half.md.
#
# THIS SCRIPT USED TO COMPOSE ITS OWN. Those four lines carried none of the
# Producer register's shape (no sections, no evidence link, a bare count in
# every line), and `producer-check --gate` walks production/briefs/ treating
# every file there as a brief. It runs inside ledger/verify.py, so the first
# night that committed a fallback would have reddened not just that file but
# every commit after it, on a machine nobody was watching at 3am.
#
# NEVER FATAL, for the same reason the dashboard block above is not: a night
# that stops because a brief refused to write would be the instrument breaking
# the work it measures. It says so and ends, and the silence is never mute.
$briefDay = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd")
$briefRel = "production/briefs/" + $briefDay + ".md"
if ($py) {
    & $py "tools/morning-brief.py" --date $briefDay 2>&1 | Write-Host
    if ($LASTEXITCODE -ne 0) {
        Write-Host ("The brief tool refused to write (exit {0}); nothing was staged and the morning has no brief. Its own output above names the source it could not read." -f $LASTEXITCODE)
    } elseif (Test-Path $briefRel) {
        # STAGE BY NAME, never `git add production/briefs`: a failed run would
        # otherwise commit its stale checkout's files as its own evidence
        # (.claude/rules/ci.md).
        git add -- $briefRel
        git diff --cached --quiet
        if ($LASTEXITCODE -ne 0) { git commit -m ("Morning brief, " + $briefDay) 2>$null }
        git push -u origin $night 2>$null
    } else {
        Write-Host ("The brief tool reported success and wrote no file at {0}; nothing staged. Success and a written file are different facts." -f $briefRel)
    }
} else {
    Write-Host "No python found, so no brief was written this night. production/briefs/ carries nothing new and that is the honest state of it."
}
# latest.md IS NOT WRITTEN HERE, and this is the one place that used to.
# It is a moving name on producer-check's frozen PRE_REGISTER list (queue 074):
# a copy carrying no exempt marker reddens the gate, and a copy carrying one
# would be a false record, since a generated file does not predate the
# register. tools/morning-brief.py refuses it under --latest for that reason
# and prints latestWritten=0/1. The dated file above is the brief.
# A toast if the machine is awake; silence is fine, the brief is the record.
try { New-BurntToastNotification -Text "LEDGER night done" -ErrorAction Stop } catch {
    msg * ("LEDGER night runner finished. Brief: " + $briefRel) 2>$null }
