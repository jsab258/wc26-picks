# LEDGER - what is this machine? Writes machine.json and nothing else.
#
# WHY A SEPARATE FILE: we do not know Jafar's GPU. The whole design branches on
# what this finds, so it is the one step that must never die quietly. Every
# lookup is wrapped: a failed probe writes a field saying it failed, because
# "no GPU found" and "the probe crashed" look identical downstream and only one
# of them means buy a graphics card.
#
# wmic is NOT used - it is removed from current Windows 11 builds. CIM is.
param([string]$Out = "machine.json", [string]$Drive = "C:")

$ErrorActionPreference = "Continue"
$m = [ordered]@{ probe = "ok"; probe_notes = @() }

function Try-Step($name, $block) {
    try { & $block } catch { $m.probe_notes += "$name failed: $($_.Exception.Message)" ; $null }
}

$m.hostname = $env:COMPUTERNAME
Try-Step "os" { $os = Get-CimInstance Win32_OperatingSystem
                $m.os = $os.Caption; $m.os_build = $os.BuildNumber
                $m.ram_bytes = [int64]$os.TotalVisibleMemorySize * 1024 }
Try-Step "cpu" { $cpu = @(Get-CimInstance Win32_Processor)[0]
                 $m.cpu = $cpu.Name.Trim(); $m.cpu_cores = $cpu.NumberOfCores }
Try-Step "ram" { $m.ram_bytes = [int64](Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory }
Try-Step "disk" { $d = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='$Drive'"
                  $m.free_disk_bytes = [int64]$d.FreeSpace; $m.disk_letter = $Drive }

# THE VRAM PROBLEM, STATED. Win32_VideoController.AdapterRAM is a uint32: every
# card above 4GB reports exactly 4294967295 and there is no way to tell that
# from an actual 4GB card. The registry's HardwareInformation.qwMemorySize is
# 64-bit and correct. We emit BOTH, per adapter, and let the planner decide -
# a single "vram" field here would be a number nobody could check.
$gpus = @()
$regAdapters = @()
Try-Step "registry vram" {
    $base = "HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
    foreach ($k in Get-ChildItem $base -ErrorAction SilentlyContinue) {
        $p = Get-ItemProperty $k.PSPath -ErrorAction SilentlyContinue
        if ($null -eq $p.DriverDesc) { continue }
        $q = $p."HardwareInformation.qwMemorySize"
        if ($q -is [byte[]]) { $q = [BitConverter]::ToInt64($q, 0) }
        $regAdapters += [ordered]@{ desc = "$($p.DriverDesc)"; qwMemorySize = [int64]($q -as [int64]) }
    }
}
Try-Step "video controllers" {
    foreach ($v in Get-CimInstance Win32_VideoController) {
        $reg = $regAdapters | Where-Object { $_.desc -eq $v.Name } | Select-Object -First 1
        if (-not $reg) { $reg = $regAdapters | Sort-Object qwMemorySize -Descending | Select-Object -First 1 }
        $gpus += [ordered]@{
            name                = "$($v.Name)"
            driver              = "$($v.DriverVersion)"
            driver_date         = "$($v.DriverDate)"
            vendor              = "$($v.AdapterCompatibility)"
            mode                = "$($v.VideoModeDescription)"
            vram_bytes          = [int64]($v.AdapterRAM -as [int64])
            vram_bytes_registry = [int64]($(if ($reg) { $reg.qwMemorySize } else { 0 }))
        }
    }
}
$m.gpus = @($gpus)
$m.registry_adapters = @($regAdapters)
if ($gpus.Count -eq 0) { $m.probe_notes += "NO display adapter returned by Win32_VideoController" }

# Which GPU APIs the drivers have actually registered. Vulkan is what the
# generator uses; DirectML is recorded because the speech pipeline runs on it
# and it is the strongest evidence we have about this machine's vendor.
Try-Step "vulkan" {
    $vk = 0
    foreach ($p in @("HKLM:\SOFTWARE\Khronos\Vulkan\Drivers",
                     "HKLM:\SOFTWARE\WOW6432Node\Khronos\Vulkan\Drivers")) {
        if (Test-Path $p) { $vk += @((Get-Item $p).GetValueNames()).Count }
    }
    $m.vulkan_drivers = $vk
}
Try-Step "directml" {
    $m.directml = $(if (Test-Path "$env:WINDIR\System32\DirectML.dll") { "present" } else { "absent" })
}
Try-Step "python" {
    $py = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
    if (-not $py) { $py = (Get-Command py.exe -ErrorAction SilentlyContinue).Source }
    $m.python = $(if ($py) { $py } else { "none on PATH" })
}

if ($m.probe_notes.Count -gt 0) { $m.probe = "partial: " + ($m.probe_notes -join " | ") }
$m | ConvertTo-Json -Depth 5 | Out-File -FilePath $Out -Encoding utf8
Write-Host "  machine probe written to $Out"
