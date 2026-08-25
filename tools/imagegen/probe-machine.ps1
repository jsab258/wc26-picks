# LEDGER - what is this machine? Writes machine.json and nothing else.
#
# WHY A SEPARATE FILE: we do not know Jafar's GPU. The whole design branches on
# what this finds, so it is the one step that must never die quietly. Every
# lookup is wrapped: a failed probe writes a field saying it failed, because
# "no GPU found" and "the probe crashed" look identical downstream and only one
# of them means buy a graphics card.
#
# VERSION 2, AND WHY. Version 1 RAN on Jafar's machine and reported
# "GPUs NONE FOUND" on a Ryzen 5 5600X - a CPU with no integrated graphics at
# all, in a box that runs Unity builds and a DirectML speech model. A discrete
# card is certainly present, so NONE FOUND was a probe bug, and it cost ten of
# twelve images (CPU fallback, 202s each). It reported, twice:
#
#   registry vram failed: Item has already been added. Key in dictionary:
#     'desc'  Key being added: 'desc'
#   video controllers failed: Item has already been added. Key in dictionary:
#     'name'  Key being added: 'name'
#
# 'desc' and 'name' are OUR OWN lowercase keys - they appear nowhere in WMI, in
# CIM or in the registry, both are the FIRST key of one of the two
# `[ordered]@{...}` row literals version 1 built inside its adapter loops, and
# that literal is the only .Add()-into-a-dictionary in the whole script. (A
# property set like `$m.ram_bytes = ...` is not: version 1 set that key twice
# and never threw.) A duplicate Add of a row's own first key cannot happen on
# the FIRST adapter, only on the second and later - which is exactly the
# multi-adapter machine, and exactly the shape the selftest never had. Every
# real desktop has several video "controllers": the card, usually a Microsoft
# Basic Display Adapter, often a virtual or remote-desktop one.
#
# NOT REPRODUCED. There is no PowerShell on the machine this was written on, so
# the exact evaluation route was never executed. That is why this version does
# not rest on the diagnosis: it removes the .Add() path entirely (rows are
# built with the INDEXER, which overwrites and cannot throw), it wraps every
# single row so one bad adapter cannot abort the enumeration, and it tries six
# independent sources instead of one. A partial answer beats none.
#
# AND A SECOND FAULT, INDEPENDENT AND ON ITS OWN SUFFICIENT: version 1
# accumulated with `$gpus += ...` inside a scriptblock invoked with `&`, which
# runs in a CHILD SCOPE. A variable ASSIGNMENT there writes a local and is
# discarded when the block ends - so `$m.gpus` would have been empty even if
# nothing had thrown. `$m.<key> = ...` survived because it mutates an object
# rather than a variable, which is why the report carried os, cpu, ram, vulkan
# and directml and lost only the two lists. Everything here accumulates by
# MUTATING an ArrayList and reads script scope explicitly, so neither can
# recur.
#
# wmic.exe is NOT used - it is removed from current Windows 11 builds. CIM is,
# and Get-WmiObject (which is not wmic.exe, and is present in Windows
# PowerShell 5.1) is one of the fallbacks.
param([string]$Out = "machine.json", [string]$Drive = "C:")

$ErrorActionPreference = "Continue"

$m = [ordered]@{}
$m["probe"] = "ok"
$m["probe_version"] = 2

$script:notes      = New-Object System.Collections.ArrayList
$script:gpus       = New-Object System.Collections.ArrayList
$script:regAdapters= New-Object System.Collections.ArrayList
$script:sourceLog  = New-Object System.Collections.ArrayList
$script:gpuSource  = ""
$script:rowsSeen   = 0
$script:rowsBad    = 0

function Note([string]$s) { [void]$script:notes.Add($s) }

function New-Ordered {
    # Built empty and filled through the INDEXER by every caller. The indexer
    # overwrites; .Add() throws "Item has already been added". Version 1's
    # crash was an Add, so there are none left in this file.
    New-Object System.Collections.Specialized.OrderedDictionary
}

function Try-Step([string]$name, [scriptblock]$block) {
    try { & $block } catch { Note "$name failed: $($_.Exception.Message)" }
}

$m["hostname"] = $env:COMPUTERNAME
Try-Step "os" { $os = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
                $m["os"] = "$($os.Caption)"; $m["os_build"] = "$($os.BuildNumber)"
                $m["ram_bytes"] = [int64]$os.TotalVisibleMemorySize * 1024 }
Try-Step "cpu" { $cpu = @(Get-CimInstance Win32_Processor -ErrorAction Stop)[0]
                 $m["cpu"] = "$($cpu.Name)".Trim(); $m["cpu_cores"] = [int]$cpu.NumberOfCores }
Try-Step "ram" { $m["ram_bytes"] = [int64](Get-CimInstance Win32_ComputerSystem -ErrorAction Stop).TotalPhysicalMemory }
Try-Step "disk" { $d = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='$Drive'" -ErrorAction Stop
                  $m["free_disk_bytes"] = [int64]$d.FreeSpace; $m["disk_letter"] = $Drive }

# ---------------------------------------------------------------------------
# THE VRAM PROBLEM, STATED. Win32_VideoController.AdapterRAM is a uint32: every
# card above 4GB reports exactly 4294967295 and there is no way to tell that
# from an actual 4GB card. The registry's HardwareInformation.qwMemorySize is
# 64-bit and correct. We emit BOTH, per adapter, and let the planner decide -
# a single "vram" field here would be a number nobody could check.
# ---------------------------------------------------------------------------
Try-Step "registry vram" {
    $base = "HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
    foreach ($k in @(Get-ChildItem $base -ErrorAction SilentlyContinue)) {
        # PER-KEY, so a single unreadable subkey costs one adapter and not all
        # of them. This loop is where version 1 died on its second row.
        try {
            $p = Get-ItemProperty $k.PSPath -ErrorAction SilentlyContinue
            if ($null -eq $p) { continue }
            if ($null -eq $p.DriverDesc) { continue }
            $q = $p."HardwareInformation.qwMemorySize"
            if ($q -is [byte[]]) { $q = [BitConverter]::ToInt64($q, 0) }
            $row = New-Ordered
            $row["desc"]         = "$($p.DriverDesc)"
            $row["key"]          = "$($k.PSChildName)"
            $row["qwMemorySize"] = [int64]($q -as [int64])
            [void]$script:regAdapters.Add($row)
        } catch {
            Note "registry adapter $($k.PSChildName) unreadable: $($_.Exception.Message)"
        }
    }
}

function Get-RegistryVram([string]$name) {
    # Returns bytes + HOW it was matched, because on a multi-adapter machine
    # "the biggest number wins for every adapter" (version 1's fallback) hands
    # the Basic Display Adapter the real card's VRAM and reads as measurement.
    $r = New-Ordered
    $r["bytes"] = [int64]0
    $r["how"]   = "no registry adapter matched"
    $n = "$name".Trim()
    $best = $null
    foreach ($a in $script:regAdapters) {
        if ("$($a['desc'])".Trim() -ieq $n) {
            if (($null -eq $best) -or ([int64]$a['qwMemorySize'] -gt [int64]$best['qwMemorySize'])) { $best = $a }
        }
    }
    if ($null -ne $best) {
        $r["bytes"] = [int64]$best['qwMemorySize']
        $r["how"]   = "exact name match"
        return $r
    }
    $withMem = @($script:regAdapters | Where-Object { [int64]$_['qwMemorySize'] -gt 0 })
    if ($withMem.Count -eq 1) {
        $r["bytes"] = [int64]$withMem[0]['qwMemorySize']
        $r["how"]   = "no name match; the only registry adapter reporting memory"
    } elseif ($withMem.Count -gt 1) {
        $r["how"]   = "no name match; $($withMem.Count) registry adapters report memory - not guessing"
    }
    return $r
}

function Add-Gpu([string]$name, [string]$driver, [string]$date, [string]$vendor,
                 [string]$mode, $ram, [string]$source) {
    # A NAMELESS ROW IS NOT AN ADAPTER, and admitting one would be worse than
    # finding nothing: plan() reads vendor off the joined names, so a blank row
    # turns "no display adapter - CPU only" into "some other vendor - use
    # Vulkan", which is a GPU claim made out of an empty string. XML paths that
    # do not exist enumerate as one $null in PowerShell, so this is reachable.
    if ("$name".Trim() -eq "") {
        Note "$source returned a row with no name - not counted as an adapter"
        return
    }
    $reg = Get-RegistryVram $name
    $row = New-Ordered
    $row["name"]                = "$name"
    $row["driver"]              = "$driver"
    $row["driver_date"]         = "$date"
    $row["vendor"]              = "$vendor"
    $row["mode"]                = "$mode"
    $row["vram_bytes"]          = [int64]($ram -as [int64])
    $row["vram_bytes_registry"] = [int64]$reg["bytes"]
    $row["vram_match"]          = "$($reg['how'])"
    $row["source"]              = "$source"
    [void]$script:gpus.Add($row)
}

function Try-Source([string]$label, [scriptblock]$block) {
    # First source that returns anything wins; every source that ran is logged
    # with how many rows it SAW, so "0 adapters" arrives with its denominator
    # instead of looking like a machine with no graphics card.
    if ($script:gpus.Count -gt 0) { return }
    $before = $script:gpus.Count
    $script:rowsSeen = 0
    $script:rowsBad  = 0
    $err = ""
    try { & $block | Out-Null } catch { $err = "$($_.Exception.Message)" }
    $got = $script:gpus.Count - $before
    $line = "$label -> $got adapter(s) from $($script:rowsSeen) row(s) seen"
    if ($script:rowsBad -gt 0) { $line += "; $($script:rowsBad) row(s) unreadable" }
    if ($err -ne "")           { $line += "; ENUMERATION FAILED: $err" }
    [void]$script:sourceLog.Add($line)
    if ($got -gt 0 -and $script:gpuSource -eq "") { $script:gpuSource = $label }
}

Try-Source "Win32_VideoController (CIM)" {
    foreach ($v in @(Get-CimInstance Win32_VideoController -ErrorAction Stop)) {
        try {
            $script:rowsSeen++
            Add-Gpu "$($v.Name)" "$($v.DriverVersion)" "$($v.DriverDate)" `
                    "$($v.AdapterCompatibility)" "$($v.VideoModeDescription)" `
                    $v.AdapterRAM "Win32_VideoController (CIM)"
        } catch { $script:rowsBad++; Note "Win32_VideoController row skipped: $($_.Exception.Message)" }
    }
}

Try-Source "CIM_VideoController (CIM)" {
    foreach ($v in @(Get-CimInstance CIM_VideoController -ErrorAction Stop)) {
        try {
            $script:rowsSeen++
            Add-Gpu "$($v.Name)" "$($v.DriverVersion)" "$($v.DriverDate)" `
                    "$($v.AdapterCompatibility)" "$($v.VideoModeDescription)" `
                    $v.AdapterRAM "CIM_VideoController (CIM)"
        } catch { $script:rowsBad++; Note "CIM_VideoController row skipped: $($_.Exception.Message)" }
    }
}

Try-Source "Win32_VideoController (WMI)" {
    # A different pipe to the same provider: Get-WmiObject is the old DCOM
    # client, not wmic.exe, and is present in Windows PowerShell 5.1. If the
    # CIM cmdlet is what mangles a duplicate row, this route does not.
    if ($null -eq (Get-Command Get-WmiObject -ErrorAction SilentlyContinue)) {
        throw "Get-WmiObject not available (PowerShell 6+ removed it)"
    }
    foreach ($v in @(Get-WmiObject Win32_VideoController -ErrorAction Stop)) {
        try {
            $script:rowsSeen++
            Add-Gpu "$($v.Name)" "$($v.DriverVersion)" "$($v.DriverDate)" `
                    "$($v.AdapterCompatibility)" "$($v.VideoModeDescription)" `
                    $v.AdapterRAM "Win32_VideoController (WMI)"
        } catch { $script:rowsBad++; Note "WMI video row skipped: $($_.Exception.Message)" }
    }
}

Try-Source "Win32_PnPEntity PNPClass=Display" {
    foreach ($v in @(Get-CimInstance Win32_PnPEntity -Filter "PNPClass='Display'" -ErrorAction Stop)) {
        try {
            $script:rowsSeen++
            Add-Gpu "$($v.Name)" "$($v.Service)" "" "$($v.Manufacturer)" "" 0 `
                    "Win32_PnPEntity PNPClass=Display"
        } catch { $script:rowsBad++; Note "PnPEntity row skipped: $($_.Exception.Message)" }
    }
}

Try-Source "display class registry" {
    # No WMI at all. The same subkeys the VRAM read already walked - if a card
    # has a driver installed, DriverDesc is there.
    foreach ($a in @($script:regAdapters)) {
        try {
            $script:rowsSeen++
            Add-Gpu "$($a['desc'])" "" "" "" "" 0 "display class registry"
        } catch { $script:rowsBad++; Note "registry-derived row skipped: $($_.Exception.Message)" }
    }
}

Try-Source "dxdiag /x" {
    # LAST, because it costs 20-60 seconds. /whql:off stops it reaching the
    # network. Its DisplayMemory is a 64-bit figure in MB, so it is also the
    # only source here that can contradict the uint32 ceiling on its own.
    $tmp = Join-Path $env:TEMP "ledger-dxdiag.xml"
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
    $proc = Start-Process -FilePath "dxdiag.exe" -ArgumentList "/whql:off","/x",$tmp `
                          -PassThru -WindowStyle Hidden -ErrorAction Stop
    Wait-Process -InputObject $proc -Timeout 120 -ErrorAction SilentlyContinue
    if (-not (Test-Path $tmp)) { throw "dxdiag wrote no XML within 120s" }
    [xml]$x = Get-Content $tmp -Raw -ErrorAction Stop
    foreach ($d in @($x.DxDiag.DisplayDevices.DisplayDevice)) {
        try {
            $script:rowsSeen++
            $bytes = 0
            if ("$($d.DisplayMemory)" -match '([\d,]+)\s*MB') {
                $bytes = [int64]("$($matches[1])" -replace ',', '') * 1MB
            }
            Add-Gpu "$($d.CardName)" "$($d.DriverVersion)" "$($d.DriverDate)" `
                    "$($d.Manufacturer)" "$($d.CurrentMode)" $bytes "dxdiag /x"
        } catch { $script:rowsBad++; Note "dxdiag row skipped: $($_.Exception.Message)" }
    }
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
}

$m["gpus"] = @($script:gpus)
$m["registry_adapters"] = @($script:regAdapters)
$m["gpu_source"] = $(if ($script:gpuSource -ne "") { $script:gpuSource } else { "none answered" })
$m["gpu_sources_tried"] = ($script:sourceLog -join " | ")
if ($script:gpus.Count -eq 0) {
    Note "NO display adapter from ANY of $($script:sourceLog.Count) sources"
}

# ---------------------------------------------------------------------------
# Which GPU APIs the drivers have actually registered. Vulkan is what the
# generator uses; DirectML is recorded because the speech pipeline runs on it
# and it is the strongest evidence we have about this machine's vendor.
#
# THIS COUNT IS INDEPENDENT OF THE ADAPTER ENUMERATION ABOVE - it reads the
# Khronos registry keys and nothing else, so version 1's "0" was NOT a
# casualty of its crash (it recorded no failure for this step). What version 1
# could not do is tell "no ICD registered" from "we could not look", and those
# want different actions, so the status is now a sentence set BEFORE the probe
# runs and overwritten only on success.
# ---------------------------------------------------------------------------
$m["vulkan_drivers"] = "unknown"
$m["vulkan_status"]  = "could not tell - the vulkan probe did not complete"
$m["vulkan_icds"]    = ""
$m["vulkan_loader"]  = "unknown"
Try-Step "vulkan" {
    $icds = New-Object System.Collections.ArrayList
    $keys = New-Object System.Collections.ArrayList
    foreach ($p in @("HKLM:\SOFTWARE\Khronos\Vulkan\Drivers",
                     "HKLM:\SOFTWARE\WOW6432Node\Khronos\Vulkan\Drivers")) {
        if (Test-Path $p) {
            [void]$keys.Add($p)
            foreach ($n in @((Get-Item $p).GetValueNames())) {
                if ("$n".Length -gt 0) { [void]$icds.Add("$n") }
            }
        }
    }
    $loader = "absent"
    foreach ($dll in @("$env:WINDIR\System32\vulkan-1.dll", "$env:WINDIR\SysWOW64\vulkan-1.dll")) {
        if (Test-Path $dll) { $loader = "present" }
    }
    $m["vulkan_drivers"] = $icds.Count
    $m["vulkan_icds"]    = ($icds -join "; ")
    $m["vulkan_loader"]  = $loader
    if ($icds.Count -gt 0) {
        $m["vulkan_status"] = "registered: $($icds.Count) ICD(s) under $($keys.Count) Khronos key(s)"
    } elseif ($keys.Count -eq 0 -and $loader -eq "absent") {
        $m["vulkan_status"] = "NOT INSTALLED - no Khronos registry key and no vulkan-1.dll"
    } elseif ($keys.Count -eq 0) {
        $m["vulkan_status"] = "loader present but NO Khronos key - the display driver registered no Vulkan device"
    } else {
        $m["vulkan_status"] = "Khronos key present but EMPTY - no ICD registered"
    }
}
Try-Step "directml" {
    $m["directml"] = $(if (Test-Path "$env:WINDIR\System32\DirectML.dll") { "present" } else { "absent" })
}
Try-Step "python" {
    $py = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
    if (-not $py) { $py = (Get-Command py.exe -ErrorAction SilentlyContinue).Source }
    $m["python"] = $(if ($py) { "$py" } else { "none on PATH" })
}

$m["probe_notes"] = @($script:notes)
if ($script:notes.Count -gt 0) { $m["probe"] = "partial: " + ($script:notes -join " | ") }
$m | ConvertTo-Json -Depth 6 | Out-File -FilePath $Out -Encoding utf8
Write-Host "  machine probe written to $Out"
Write-Host "  adapters: $($script:gpus.Count) via $($m['gpu_source'])"
