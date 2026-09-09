# LEDGER overnight runner. WRITTEN ON THE CONTAINER, EXECUTES ON WINDOWS.
# Untested where written: this container has no PowerShell (the verify
# footer names that lint NOT CHECKED), so the first Windows run is this
# script's accepting test, per rule 5b, and should be watched end to end.
# Authority: ledger-v2/studio-v2/runner.md. Kill switch: production/STOP.
#
# CHECKOUT OWNERSHIP, AND THIS IS A HAZARD RATHER THAN A NOTE. Line 25 does
# `git checkout -B $night` in the REPOSITORY ROOT, which tools/pc-watcher.py
# hard-resets roughly once a minute while the supervisor is up. Running this
# script and "START EVERYTHING.bat" at the same time puts two writers on one
# git index, which is the fight that cost this project four days. So: this is
# still a manual double-click, and it is a double-click for a machine with the
# supervisor CLOSED.
#
# THE UNATTENDED PATH IS NOT THIS FILE ANY MORE. tools/runner/executor.py is
# the supervised daemon that takes an instruction from Telegram, runs a
# bounded session and answers; it works in a git worktree of its own beside
# the project and refuses by path to run git in here. Do not re-point either
# of them at the other's checkout. This script is left alone deliberately: its
# job (walk production/queue/ all night, rebuild the dashboard, write the
# brief) is a different job from answering one message.
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

# THE BRIEF IS NOT WRITTEN HERE ANY MORE, AND NOT BY ANY TOOL. RETIRED
# 2026-09-09 BY JAFAR, VERBATIM: "The channel fails because nobody with
# judgment sits in it. Replace the machinery with one judgment step. One
# Producer turn a day writes the single message... The brief generator, the
# cards pass and the page notifier are retired."
#
# WHAT STOOD HERE: a call to tools/morning-brief.py, which composed a brief
# from repository state, staged it and pushed it. That file is still in the
# tree with its own RETIRED banner, and nothing calls it: this was its last
# caller. It is not deleted because it is the record of what was tried.
#
# WHAT REPLACED IT: a Producer turn reads the five sources
# (tools/producer-day.py gathers them), writes production/briefs/<day>.md in
# its own words, and tools/runner/telegram-bot.py --send-brief sends it with
# two buttons on it, readable and unreadable. The night runner has no part in
# it: a machine cannot supply the judgment the ruling asks for, and a night
# that wrote a brief nobody read is exactly what was retired.
$briefDay = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd")
$briefRel = "production/briefs/" + $briefDay + ".md"
if (Test-Path $briefRel) {
    Write-Host ("A brief for today is already written at {0}; this run neither wrote it nor sent it." -f $briefRel)
} else {
    Write-Host ("No brief for {0} yet. Nothing here writes one: one Producer turn a day does, and --send-brief sends it." -f $briefDay)
}
# A toast if the machine is awake; silence is fine, the brief is the record.
try { New-BurntToastNotification -Text "LEDGER night done" -ErrorAction Stop } catch {
    msg * ("LEDGER night runner finished. Brief: " + $briefRel) 2>$null }
