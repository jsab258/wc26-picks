# LEDGER - what TOOLCHAIN is on this machine? Writes tools.json and nothing else.
#
# WHY THIS IS A SECOND PROBE AND NOT A BIGGER FIRST ONE. tools/imagegen/
# probe-machine.ps1 answers "what hardware is this" - adapters, VRAM, RAM,
# disk - and it answers it carefully, over six sources, after version 1 of it
# reported NO GPU on a machine with a discrete card. That file is reused as it
# stands and is not touched: a second copy of adapter detection would be a
# second copy of its bugs. This file answers a DIFFERENT question, which that
# one has no reason to ask: is the toolchain here that a mesh pipeline needs.
#
# NEVER GUESSES. Every lookup is wrapped, every failure is recorded as a note,
# and a value that could not be read is written as the empty string rather than
# as a plausible default. A zero here ships its denominator the same way the
# hardware probe's does: `sources_tried` says how hard it looked.
#
# UNRUN WHERE IT WAS WRITTEN. There is no PowerShell in the container this was
# authored in, so this file has never executed. meshgen.py's decisions are all
# made from the JSON it produces and are tested there against fixtures,
# including a fixture of the file being ABSENT - which must read as "nobody
# looked", never as "the machine has nothing".
param([string]$Out = "tools.json")

$ErrorActionPreference = "Continue"
$t = [ordered]@{}
$t["probe"] = "ok"
$t["probe_version"] = 1
$t["written"] = (Get-Date).ToString("s")
$script:notes = New-Object System.Collections.ArrayList
$script:tried = New-Object System.Collections.ArrayList

function Note([string]$m) { [void]$script:notes.Add($m) }

function Try-Step([string]$label, [scriptblock]$block) {
    [void]$script:tried.Add($label)
    try { & $block | Out-Null }
    catch { Note "$label failed: $($_.Exception.Message)" }
}

function Where-First([string]$exe) {
    # `where.exe` returns every hit; the first is what would run.
    try {
        $r = & where.exe $exe 2>$null
        if ($LASTEXITCODE -eq 0 -and $r) { return (@($r)[0]).Trim() }
    } catch { }
    return ""
}

function Run-Line([string]$exe, [string[]]$argv) {
    # First non-empty line of a tool's own output. Tools lie in many ways but
    # they are usually honest about their version.
    try {
        $o = & $exe @argv 2>$null
        foreach ($line in @($o)) { if ("$line".Trim() -ne "") { return "$line".Trim() } }
    } catch { }
    return ""
}

# --- Blender -----------------------------------------------------------------
Try-Step "blender" {
    $p = Where-First "blender.exe"
    if (-not $p) {
        $cands = @()
        foreach ($base in @("$env:ProgramFiles\Blender Foundation",
                            "${env:ProgramFiles(x86)}\Steam\steamapps\common\Blender",
                            "$env:LOCALAPPDATA\Programs\Blender Foundation",
                            "$env:LOCALAPPDATA\Microsoft\WindowsApps")) {
            if (Test-Path $base) {
                $cands += @(Get-ChildItem -Path $base -Filter "blender.exe" -Recurse `
                              -ErrorAction SilentlyContinue | Select-Object -First 4)
            }
        }
        # Newest first: a machine with 3.6 and 4.2 should be measured on 4.2.
        $best = $cands | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($best) { $p = $best.FullName }
    }
    $t["blender"] = $p
    if ($p) { $t["blender_version"] = (Run-Line $p @("--version")) }
    else { Note "no blender.exe on PATH, under Program Files, Steam, or WindowsApps" }
}

# --- Python, conda -----------------------------------------------------------
Try-Step "python" {
    $p = Where-First "python.exe"
    if (-not $p -and (Test-Path "$env:USERPROFILE\miniconda3\python.exe")) {
        $p = "$env:USERPROFILE\miniconda3\python.exe"
    }
    $t["python"] = $p
    if ($p) {
        $v = (Run-Line $p @("-c", "import sys;print('%d.%d.%d'%sys.version_info[:3])"))
        $t["python_version"] = $v
    } else { Note "no python.exe on PATH and none at ~\miniconda3" }
}
Try-Step "conda" {
    $c = Where-First "conda.exe"
    if (-not $c -and $env:CONDA_EXE) { $c = $env:CONDA_EXE }
    if (-not $c -and (Test-Path "$env:USERPROFILE\miniconda3\Scripts\conda.exe")) {
        $c = "$env:USERPROFILE\miniconda3\Scripts\conda.exe"
    }
    $t["conda"] = $c
}

# --- CUDA, NVIDIA ------------------------------------------------------------
Try-Step "nvcc" {
    $n = Where-First "nvcc.exe"
    if (-not $n -and $env:CUDA_PATH -and (Test-Path "$env:CUDA_PATH\bin\nvcc.exe")) {
        $n = "$env:CUDA_PATH\bin\nvcc.exe"
    }
    $t["nvcc"] = $n
    if ($n) { $t["cuda_version"] = (Run-Line $n @("--version")) }
}
Try-Step "nvidia-smi" {
    $s = Where-First "nvidia-smi.exe"
    $t["nvidia_smi"] = $s
    if ($s) { $t["nvidia_smi_line"] = (Run-Line $s @("--query-gpu=name,memory.total,driver_version", "--format=csv,noheader")) }
    else { Note "no nvidia-smi: there is no NVIDIA driver on this machine, which is the whole TRELLIS question answered in one line" }
}

# --- MSVC (the CUDA submodules are C++) --------------------------------------
Try-Step "msvc" {
    $cl = Where-First "cl.exe"
    $vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
    $vs = ""
    if (Test-Path $vswhere) {
        $vs = (Run-Line $vswhere @("-latest", "-products", "*", "-requires",
                                   "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                                   "-property", "installationPath"))
    } else {
        Note "vswhere.exe is absent, so there is no Visual Studio installation of any kind (same finding as production/d1-probe/ue-machine-read.md, 1 Sep)"
    }
    if ($cl) { $t["msvc"] = $cl } elseif ($vs) { $t["msvc"] = $vs } else { $t["msvc"] = "" }
}

# --- bash and git ------------------------------------------------------------
Try-Step "bash" { $t["bash"] = (Where-First "bash.exe") }
Try-Step "git" {
    $g = Where-First "git.exe"
    $t["git"] = $g
    if ($g) { $t["git_version"] = (Run-Line $g @("--version")) }
}

# --- torch, only if a python was found ---------------------------------------
Try-Step "torch" {
    $t["torch"] = ""
    $t["torch_cuda"] = ""
    if ($t["python"]) {
        $line = (Run-Line $t["python"] @("-c", "import torch;print(torch.__version__);print(torch.cuda.is_available())"))
        if ($line) {
            $t["torch"] = $line
            $t["torch_cuda"] = (Run-Line $t["python"] @("-c", "import torch;print(torch.cuda.is_available())"))
        } else {
            Note "python has no torch installed, which is expected: nothing here installs into his Python"
        }
    }
}

# --- disk, every fixed drive -------------------------------------------------
Try-Step "disks" {
    $rows = @()
    foreach ($d in @(Get-CimInstance Win32_LogicalDisk -ErrorAction Stop | Where-Object { $_.DriveType -eq 3 })) {
        $rows += [ordered]@{ letter = "$($d.DeviceID)"; free_bytes = [int64]$d.FreeSpace; size_bytes = [int64]$d.Size }
    }
    $t["disks"] = @($rows)
}

$t["sources_tried"] = ($script:tried -join ", ")
$t["notes"] = @($script:notes)
if ($script:notes.Count -gt 0) { $t["probe"] = "partial: " + ($script:notes.Count) + " note(s)" }

$t | ConvertTo-Json -Depth 6 | Out-File -FilePath $Out -Encoding utf8
Write-Host "  toolchain probe written to $Out"
Write-Host ("  blender: " + $(if ($t["blender"]) { $t["blender"] } else { "NOT FOUND" }))
Write-Host ("  nvidia : " + $(if ($t["nvidia_smi"]) { $t["nvidia_smi_line"] } else { "NO NVIDIA DRIVER" }))
# Exit 0 always: this probe reports, it does not decide. The decision lives in
# meshgen.py, where there are tests - the same split imagegen.py uses, and the
# reason its .bat compares the hardware probe's code with == and not
# `if errorlevel`.
exit 0
