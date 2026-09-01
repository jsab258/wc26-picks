# LEDGER - where is Blender on this machine? Writes one answer file, nothing else.
#
# IT CONTAINS NO SEARCH OF ITS OWN, AND THAT IS THE POINT. probe-tools.ps1
# already knows every place Blender can be on this PC, in priority order and
# newest version first, and it names each of them in its own not-found note.
# That list is deliberately NOT restated here, in prose or in code: a second
# copy is the fault this project has now paid for three times, and a comment
# listing the locations decays into a wrong answer exactly like a second
# implementation does. Read the probe. What the missing line would have cost
# here is the portable extract, which is the only Blender on Jafar's machine.
# So this file runs that probe and reads its answer.
#
# THE COST OF REUSE, said out loud: the probe also looks for Python, CUDA,
# MSVC, git and the disks, so this takes tens of seconds rather than one. The
# caller says so in the window. The alternative was a -Only switch on the
# probe, which is an edit to the file the working prop grinder depends on,
# untestable here, to save half a minute.
#
# THE ANSWER IS A FILE, NOT AN EXIT CODE OR STDOUT. The probe writes with
# Write-Host, which lands in the same redirected stream as anything this
# script printed, so a caller reading stdout would have to filter the probe's
# own chatter. A file cannot be confused with it. Line 1 is the blender path
# or EMPTY; every line after it says where the search looked, so "not found"
# ships the search it is the answer to and cmd can just print the file.
#
# UNRUN WHERE IT WAS WRITTEN. There is no PowerShell in the container this was
# authored in. The first double-click of "3 LOOK AT THE PROPS.bat" is its
# accepting case.
param(
    [string]$Answer = "blender-answer.txt",
    [string]$ToolsOut = ""
)

$ErrorActionPreference = "Continue"
# Resolved once, so the .NET writer at the bottom and the report path derived
# here cannot disagree about what a relative path meant.
$Answer = [System.IO.Path]::GetFullPath($Answer)
if (-not $ToolsOut -or $ToolsOut -eq "") {
    $ToolsOut = [System.IO.Path]::Combine(
        [System.IO.Path]::GetDirectoryName($Answer), "tools.json")
}

$lines = New-Object System.Collections.ArrayList
$path = ""
$version = ""

$probe = Join-Path $PSScriptRoot "probe-tools.ps1"
if (-not (Test-Path $probe)) {
    [void]$lines.Add("the toolchain probe is missing from the project:")
    [void]$lines.Add("  $probe")
    [void]$lines.Add("This usually means the project folder is incomplete. Pull it again.")
} else {
    try {
        & $probe -Out $ToolsOut | Out-Null
    } catch {
        [void]$lines.Add("the toolchain probe failed to run: $($_.Exception.Message)")
    }
    if (Test-Path $ToolsOut) {
        try {
            $raw = Get-Content -Raw -Path $ToolsOut
            # A UTF8 BOM survives some readers and breaks ConvertFrom-Json with
            # a message about an unexpected character, which reads as corrupt
            # JSON rather than as a byte order mark.
            $raw = $raw.TrimStart([char]0xFEFF)
            $t = $raw | ConvertFrom-Json
            if ($t.blender) { $path = "$($t.blender)" }
            if ($t.blender_version) { $version = "$($t.blender_version)" }
            if (-not $path) {
                [void]$lines.Add("The toolchain probe found no blender.exe. Where it looked:")
                foreach ($n in @($t.notes)) {
                    if ("$n" -match "blender") { [void]$lines.Add("  $n") }
                }
                [void]$lines.Add("  (full report: $ToolsOut)")
            }
        } catch {
            [void]$lines.Add("the toolchain report could not be read: $($_.Exception.Message)")
            [void]$lines.Add("  report: $ToolsOut")
        }
    } else {
        [void]$lines.Add("the toolchain probe produced no report at $ToolsOut,")
        [void]$lines.Add("so nothing looked for Blender. That is not the same as")
        [void]$lines.Add("Blender being absent.")
    }
}

# Line 1 is the answer and is read with cmd's `set /p`, which takes the first
# line only. An empty first line leaves the caller's variable unset, which is
# exactly the not-found signal.
$out = New-Object System.Collections.ArrayList
[void]$out.Add($path)
if ($version) { [void]$out.Add("version: $version") }
foreach ($l in $lines) { [void]$out.Add($l) }

$enc = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllLines($Answer, [string[]]$out, $enc)

if ($path) { Write-Host "  blender: $path" } else { Write-Host "  blender: NOT FOUND" }
# Exit 0 always. This reports; the caller decides, the same split probe-tools
# uses and for the same reason.
exit 0
