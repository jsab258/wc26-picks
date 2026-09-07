# ONE IDEA, ONE IMPLEMENTATION: THE THREE-WAY PROCESS READ.
#
# WHY THIS EXISTS. Ruling 2026-09-07 (B1, found reviewing
# install-scheduled-task.ps1) fixed a specific silent failure:
# -ErrorAction SilentlyContinue on a WMI process query makes "the query
# itself failed" print identically to "nothing is running", which is the
# more dangerous of the two outcomes, because a caller that cannot tell
# them apart proceeds onto a live git index, or kills nothing while
# reporting success. Both facts are carried here: the query runs with
# -ErrorAction Stop inside a try/catch, and a caller that cannot ask gets
# Ok=$false with the reason, never an empty list standing in for "none".
#
# DOT-SOURCED, NEVER RUN DIRECTLY. This file has no executable statement
# outside the one function below, so sourcing it twice, or from two
# different scripts in the same job, only defines the function again.
#
#   . (Join-Path $PSScriptRoot "process-query.ps1")
#   $r = Get-MatchingProcesses -Pattern 'tools\\runner\\telegram-bot\.py'
#   if (-not $r.Ok) { <the query failed; $r.QueryError says why> }
#   elseif ($r.Processes.Count -eq 0) { <nothing matched> }
#   elseif ($r.Processes.Count -gt 1) { <name every one> }
#   else { <the one process is $r.Processes[0]> }
#
# REUSED BY tools/runner/install-scheduled-task.ps1 (three supervisor
# patterns folded into one caller-side Kind label) and by
# tools/runner/restart-telegram-bot.ps1 (one pattern, no Kind needed) -
# the shape is one implementation either way, per the review that asked
# for it rather than a second copy of the same try/catch.
#
# CARRIES CreationDate, ADDED ON REVIEW (ruling 2026-09-07, "the remote
# restart job, and the pair of processes it would have refused", section
# 1). A venv's python.exe on Windows is a redirector that launches the
# base interpreter as a CHILD and waits for it (bpo-34977), so every
# daemon this project spawns through sys.executable is TWO processes, a
# root and a leaf, both matching the same pattern. Telling a respawned
# process apart from a reused PID needs its creation time, not its
# number; the installer's Kind labelling does not need this field and
# ignores it.

function Get-MatchingProcesses {
    param([string]$Pattern)
    try {
        $raw = @(Get-CimInstance Win32_Process `
            -Filter "Name='python.exe' OR Name='pythonw.exe'" -ErrorAction Stop)
    } catch {
        return [pscustomobject]@{
            Ok = $false
            Processes = @()
            QueryError = ($_.Exception.Message -replace '\s+', ' ')
        }
    }
    $procs = @($raw | Where-Object { $_.CommandLine -and $_.CommandLine -match $Pattern } |
      ForEach-Object {
        [pscustomobject]@{
            ProcessId = $_.ProcessId
            ParentProcessId = $_.ParentProcessId
            CommandLine = $_.CommandLine
            CreationDate = $_.CreationDate
        }
      })
    return [pscustomobject]@{ Ok = $true; Processes = $procs; QueryError = "" }
}
