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
    git push -u origin $night
}

# Brief delivery, the guaranteed path: a mechanical fallback with zero model
# calls, per runner.md. The rich brief is a queue task; if that session died,
# this still tells the morning what happened.
$briefName = "night-" + (Get-Date -Format "yyyyMMdd") + ".md"
$brief = Join-Path $repo ("production/briefs/" + $briefName)
if (-not (Test-Path $brief)) {
    $done    = (Get-ChildItem "production/queue/done"    -Filter "*.md" -File -ErrorAction SilentlyContinue | Measure-Object).Count
    $blocked = (Get-ChildItem "production/queue/blocked" -Filter "*.md" -File -ErrorAction SilentlyContinue | Measure-Object).Count
    $left    = (Get-ChildItem "production/queue"         -Filter "*.md" -File -ErrorAction SilentlyContinue |
                Where-Object { $_.Name -ne "README.md" } | Measure-Object).Count
    $gitlog  = git log --oneline ("origin/claude/game-dev-ai-automation-2h67ix.." + $night) 2>$null
    @("# Fallback brief (mechanical; the rich-brief session did not run)",
      ("night: " + $night),
      ("done: " + $done + "  blocked: " + $blocked + "  still queued: " + $left),
      "", "landed on the night branch:", $gitlog) | Set-Content $brief
}
Copy-Item $brief (Join-Path $repo "production/briefs/latest.md") -Force
git add production/briefs
git commit -m "Night brief" 2>$null
git push -u origin $night 2>$null
# A toast if the machine is awake; silence is fine, the brief is the record.
try { New-BurntToastNotification -Text "LEDGER night done" -ErrorAction Stop } catch {
    msg * "LEDGER night runner finished. Brief: production/briefs/latest.md" 2>$null }
