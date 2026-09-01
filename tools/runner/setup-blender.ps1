# LEDGER - put Blender on this machine by unpacking its portable zip.
#
# WHY THIS IS A FILE AND NOT A WORKFLOW STEP. It was a step, and it grew to
# 25,259 characters, which is 2,075 over the largest `run:` block that has
# ever been accepted by workflow_dispatch (tools/workflow-size.py, measured
# not guessed). Past that ceiling GitHub returns 422 at DISPATCH time, so the
# commit that breaks it is green, lands, and the breakage is found by whoever
# next tries to build. The repair is the one this project already made for the
# PATH bootstrap: a large script belongs in a file that the step calls, and
# tools/runner/bootstrap-paths.cmd is the shape being copied.
#
# THE COMMENTS ARE THE DELIVERABLE, same as they are in that file. Nothing was
# cut to fit; the text moved. Everything below this header is the step's own
# body, unchanged apart from the four edits that turn step scope into
# parameters (the output path, the sha, the temp directory, and the probe's
# location). Behaviour, keys, outcomes and exit codes are the same.
#
# CALLED AFTER CHECKOUT, necessarily: a script in the repository does not
# exist before the repository does. The bootstrap step has the same ordering
# constraint and the same reason.
#
# UNRUN WHERE IT WAS WRITTEN. There is no Windows and no download.blender.org
# in the container this was authored in. What IS checked here: every pwsh
# block in the repo parses (tools/ps-check.py), and the checksum parse below
# is run against six fixtures, three accepting and three rejecting
# (tools/test-blender-hash-parse.py, wired into ledger/verify.py). The first
# dispatch is the accepting case for the download and the extraction.
param(
    # The commit this run is measuring. Passed in full and truncated below;
    # GITHUB_SHA is the caller's fact and this script does not reach for it.
    [string]$Sha = "",
    # Where the report goes. Its directory is created if it is absent.
    [string]$Out = "production/mesh-reports/blender-setup.txt",
    # RUNNER_TEMP on CI. Empty falls back to $env:TEMP.
    [string]$Temp = "",
    # THE CONSUMER, and the reason any of this is worth doing: meshgen's own
    # toolchain probe, run exactly as "1 MAKE THE PROPS.bat" runs it. Named
    # here rather than hardcoded so the call site shows the dependency.
    [string]$ProbeScript = "tools\meshgen\probe-tools.ps1"
)

$ErrorActionPreference = "Continue"
# Without this, Invoke-WebRequest spends most of a 400 MB download
# drawing a progress bar into a log nobody can tail.
$ProgressPreference = "SilentlyContinue"
$script:out = $Out
$outDir = Split-Path -Parent $script:out
if ($outDir) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }
# Truncated HERE and not at the call site, so the caller passes the sha it
# has and this file owns the one format the report has ever printed.
$sha = $Sha
if ($sha) { $sha = $sha.Substring(0, [Math]::Min(7, $sha.Length)) } else { $sha = "SHA-UNKNOWN" }
$script:L = @("# Blender setup - $sha", "")
$script:L += "host=$env:COMPUTERNAME written=$((Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'))"
# Nothing has touched the machine yet, and this key must be able to
# say so even on the paths that stop early.
$script:changed = "no"
# RUNNER_TEMP comes in as a parameter because it is the CALLER's fact, not
# this machine's; $env:TEMP stays as the fallback exactly as before, so a
# hand run outside CI still has somewhere to put 360 MB.
$tmp = if ($Temp) { $Temp } else { $env:TEMP }

# ONE ENDING, so every exit writes the file, prints it, and carries
# the same three keys. An early stop that forgot one of them would
# leave the commit step unable to tell "did not run" from "ran and
# found nothing".
function Finish([string]$outcome) {
  $script:L += "changedMachine=$script:changed"
  $script:L += "outcome=$outcome"
  $script:L += "setupReached=end"
  $script:L | Set-Content $script:out -Encoding utf8
  Write-Host ($script:L -join "`n")
}
# Paths on Windows have spaces in them and a verdict value may not.
function Tilde([string]$s) { if ($s) { return ($s -replace ' ', '~') } else { return "none" } }

# ASK THE CONSUMER WHERE IT LOOKS - DO NOT RE-IMPLEMENT ITS LOOKUP.
# An install that lands somewhere meshgen does not search would
# "succeed" here and the batch would still refuse, so the test is
# meshgen's own probe, run the same way its .bat runs it (Windows
# PowerShell, -NoProfile -ExecutionPolicy Bypass). It writes one
# JSON to the path it is given and touches nothing else.
# "NOBODY LOOKED" MUST NOT READ AS "NOT THERE", so the flag below
# says whether the probe produced a reading at all, and a probe that
# wrote nothing prints its own last lines rather than being folded
# into a silent empty answer.
$script:probeWrote = "no"
function Get-BlenderPath {
  $j = Join-Path $tmp "blender-setup-tools.json"
  if (Test-Path $j) { Remove-Item $j -Force -ErrorAction SilentlyContinue }
  $probeOut = @(& powershell -NoProfile -ExecutionPolicy Bypass -File $ProbeScript -Out $j 2>&1)
  if (-not (Test-Path $j)) {
    $script:probeWrote = "no"
    $script:L += "note: meshgen's probe wrote no JSON at $j, so it did not run. That is not the same finding as Blender being absent."
    $tail = @($probeOut | Select-Object -Last 5)
    if ($probeOut.Count -gt $tail.Count) { $script:L += "(+$($probeOut.Count - $tail.Count) earlier probe output lines not shown)" }
    foreach ($ln in $tail) { $script:L += "probe: $ln" }
    return ""
  }
  $script:probeWrote = "yes"
  try {
    $raw = (Get-Content $j -Raw).TrimStart([char]0xFEFF)
    $t = $raw | ConvertFrom-Json
  } catch {
    $script:probeWrote = "unreadable"
    $script:L += "note: the probe's JSON at $j could not be parsed: $($_.Exception.Message)"
    return ""
  }
  if ($t.blender) { return "$($t.blender)" }
  return ""
}

$before = Get-BlenderPath
if ($before) {
  $script:L += "presentBeforeThisRun=yes"
  $script:L += "ALREADY PRESENT: meshgen's probe found blender.exe before this run."
  $script:L += "Nothing was downloaded and nothing was unpacked. Verification below still RAN it."
} else {
  $script:L += "presentBeforeThisRun=no"
  $script:L += "not present: meshgen's probe found no blender.exe, so this run unpacks one."
  # THE METHOD IS IN THE REPORT, NOT ONLY IN THIS FILE. Whoever
  # reads blender-setup.txt on the machine cannot see this comment,
  # and "why is it not using the installer any more" is the first
  # question the next reader of that file will have.
  $script:L += "method=portable-zip"
  $script:L += "note: this step no longer runs an installer. The MSI path was DELETED on 1 Sep, not kept as a fallback, because msiexec returned 1603 here (rights: a per-machine MSI needs an elevated runner service) and the same PC has already refused the PowerShell 7 installer. Blender's portable zip is the same build and needs no elevation. If you want the MSI back it comes back as its own named step with its own keys."

  # DISCOVER THE DOWNLOAD, NEVER GUESS ITS URL. A hardcoded version
  # 404s the day Blender ships a patch, and a failed guess costs a
  # round trip on a machine nobody here can log into. If the index
  # cannot be read this step STOPS; there is no fallback URL,
  # because a fallback is the guess with extra steps.
  $indexUrl = "https://download.blender.org/release/"
  $script:L += "reading the release index: $indexUrl"
  $idx = $null
  try { $idx = Invoke-WebRequest -Uri $indexUrl -UseBasicParsing -TimeoutSec 120 }
  catch { $script:L += "INDEX UNREADABLE: $($_.Exception.Message)" }
  if (-not $idx) {
    $script:L += "indexRead=no"
    $script:L += "STOPPING: no index, no version, and this step does not fall back to a guessed URL."
    Finish "failed"; exit 1
  }
  $script:L += "indexRead=yes indexBytes=$($idx.Content.Length)"

  $seen = @{}
  foreach ($m in [regex]::Matches($idx.Content, 'Blender(\d+)\.(\d+)/')) {
    $seen["$($m.Groups[1].Value).$($m.Groups[2].Value)"] = $true
  }
  $sortedLines = @($seen.Keys | Sort-Object { [version]$_ } -Descending)
  $script:L += "lineDirsSeen=$($seen.Count)"
  if ($seen.Count -gt 0) { $script:L += "newestLineInIndex=$($sortedLines[0])" }

  # WHICH LINE IS LTS IS A CLAIM, AND CLAIMS DECAY. The patch is
  # discovered; the LINE comes from this named list, newest first,
  # because "is 4.5 an LTS" is not derivable from a directory
  # listing. The report prints the newest line the index actually
  # has beside the one chosen, so the day this list goes stale is
  # a line in the report rather than a silent old install.
  # LTS is deliberate: tools/meshgen/blender/clean_lod.py has never
  # been run against a real bpy, so the conservative line is the
  # one upstream keeps fixing for two years.
  $ltsPreference = @("4.5", "4.2", "3.6", "3.3")
  $script:L += "ltsPreference=$($ltsPreference -join ',')"
  $chosen = ""
  foreach ($v in $ltsPreference) { if ($seen.ContainsKey($v)) { $chosen = $v; break } }
  if (-not $chosen) {
    $script:L += "ltsLineChosen=none"
    $script:L += "STOPPING: the index has $($seen.Count) release line(s) and none of them is on the LTS list above."
    Finish "failed"; exit 1
  }
  $script:L += "ltsLineChosen=$chosen"
  if ($sortedLines.Count -gt 0 -and $sortedLines[0] -ne $chosen) {
    $script:L += "note: the newest line in the index is $($sortedLines[0]), which is not on the LTS list. If it has become an LTS line, add it to ltsPreference in this workflow."
  }

  $lineUrl = $indexUrl + "Blender$chosen/"
  $script:L += "reading the line index: $lineUrl"
  $dir = $null
  try { $dir = Invoke-WebRequest -Uri $lineUrl -UseBasicParsing -TimeoutSec 120 }
  catch { $script:L += "LINE INDEX UNREADABLE: $($_.Exception.Message)" }
  if (-not $dir) {
    $script:L += "lineIndexRead=no"
    $script:L += "STOPPING: the chosen line's directory could not be read."
    Finish "failed"; exit 1
  }
  $script:L += "lineIndexRead=yes lineIndexBytes=$($dir.Content.Length)"

  # Every filename appears twice in an autoindex row (the href and
  # the link text), so the hashtable is what makes the count a
  # count of FILES rather than of mentions.
  #
  # THE PORTABLE ZIP, AND THE MSI PATH IS GONE RATHER THAN KEPT AS
  # A FALLBACK. The run of 1 Sep discovered the version correctly,
  # downloaded 360 MB, and died on `msiexecExit=1603`, which under
  # /qn is rights: a per-machine MSI cannot write to Program Files
  # from a runner service that is not elevated. This machine has
  # form for exactly that - tools/runner/3 FINISH THE BUILD
  # MACHINE.bat exists because Windows installer service refused
  # PowerShell 7 at 92% with "Access is denied" on this same PC,
  # and unpacks a plain zip instead.
  #
  # So the MSI is not a fallback here, it is a known negative on
  # the only machine this workflow runs on, and keeping it would
  # mean a second implementation of "put Blender on this PC" whose
  # job is to fail slowly after a 360 MB download. Blender ships
  # the same version as a portable zip in the same directory:
  # extracting needs no installer, no elevation, no reboot and no
  # registry, which removes the failure class instead of fighting
  # it. If a future machine somehow needs the MSI, it comes back as
  # a named step with its own report keys, not as a silent retry.
  $files = @{}
  foreach ($m in [regex]::Matches($dir.Content, 'blender-(\d+)\.(\d+)\.(\d+)-windows-?(?:x64|64)\.zip(?![\w.])')) {
    $files[$m.Value] = [version]("$($m.Groups[1].Value).$($m.Groups[2].Value).$($m.Groups[3].Value)")
  }
  $script:L += "zipCandidates=$($files.Count)"
  if ($files.Count -eq 0) {
    $script:L += "STOPPING: no Windows x64 ZIP matched in $lineUrl. The page was read ($($dir.Content.Length) bytes) and contained no filename of the form blender-N.N.N-windows-x64.zip."
    Finish "failed"; exit 1
  }
  $best = @($files.GetEnumerator() | Sort-Object -Property Value -Descending)[0]
  $file = $best.Key
  $ver = $best.Value.ToString()
  $url = $lineUrl + $file
  $script:L += "blenderVersionChosen=$ver"
  $script:L += "blenderZipUrl=$url"
  $script:L += "note: three keys changed name with the method, so a diff against the run of 1 Sep reads as a change of method rather than a missing key: blenderMsiUrl is now blenderZipUrl, msiCandidates is now zipCandidates, and outcome=installed is now outcome=extracted. Every discovery key above is unchanged."

  # WHERE IT GOES, AND WHY NOT SOMEWHERE THE PROBE ALREADY LOOKED.
  # C:\LedgerTools is this project's established unprivileged tool
  # root: bootstrap-paths.cmd looks for pwsh under it and the
  # Windows build unpacks a python zip into it, both from this same
  # service account. The consumer is taught to look there, in
  # tools/meshgen/probe-tools.ps1, as the FIRST entry of its search
  # list.
  #
  # The tempting alternative was to extract into
  # %LOCALAPPDATA%\Programs\Blender Foundation, which that probe
  # already searched, and it is wrong: LOCALAPPDATA is PER ACCOUNT.
  # This workflow runs as the runner SERVICE account and
  # "1 MAKE THE PROPS.bat" is double-clicked by Jafar, so the
  # extraction would land in a profile the consumer never reads and
  # the verification below would go green on a path that cannot
  # help him. A guard passing while the consumer still refuses is
  # the failure this step exists to prevent.
  $toolsRoot = "C:\LedgerTools\blender"
  $dest = Join-Path $toolsRoot $ver
  $script:L += "extractRoot=$(Tilde $dest)"
  $script:L += "destExistedBefore=$(if (Test-Path $dest) { 'yes' } else { 'no' })"

  # THE RIGHTS TEST HAPPENS BEFORE THE 360 MB, NOT AFTER IT. The MSI
  # run spent the entire download and only then found out it could
  # not write. This writes one file, reads the answer, and stops in
  # seconds when the answer is no - and it names the exact command
  # that fixes it, because the reader of this file cannot log into
  # that machine.
  $canWrite = $false
  $writeErr = ""
  try {
    New-Item -ItemType Directory -Force -Path $dest -ErrorAction Stop | Out-Null
    $probeFile = Join-Path $dest ".ledger-write-test"
    Set-Content -Path $probeFile -Value "ledger" -ErrorAction Stop
    Remove-Item $probeFile -Force -ErrorAction SilentlyContinue
    $canWrite = $true
    # The machine has been altered from here on: this run created
    # or claimed a directory under C:\LedgerTools.
    $script:changed = "yes"
  } catch { $writeErr = $_.Exception.Message }
  if (-not $canWrite) {
    $script:L += "writeTest=refused"
    if ($writeErr) { $script:L += "note: the write test threw: $writeErr" }
    $script:L += "STOPPING: this account cannot write to $dest, so nothing could land there. NOTHING WAS DOWNLOADED."
    $script:L += "fix: on the runner, in an administrator command prompt, run this one line and dispatch again:"
    $script:L += "fix:   icacls C:\LedgerTools /grant Users:(OI)(CI)M"
    Finish "failed"; exit 1
  }
  $script:L += "writeTest=ok"

  $zip = Join-Path $tmp $file
  try { Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing -TimeoutSec 1800 }
  catch {
    $script:L += "DOWNLOAD FAILED: $($_.Exception.Message)"
    Finish "failed"; exit 1
  }
  $bytes = (Get-Item $zip).Length
  $script:L += "downloadedBytes=$bytes"
  if ($bytes -lt 50000000) {
    $script:L += "STOPPING: a Blender release archive is a few hundred MB. $bytes bytes is an error page, not a zip."
    Finish "failed"; exit 1
  }

  # TWO PLACES THE HASH CAN LIVE, AND BOTH ARE TRIED. The MSI run
  # reported checksum=not-published after reading exactly one URL,
  # <file>.sha256, and concluded upstream publishes nothing. That
  # conclusion was never tested against the other shape: Blender
  # also ships ONE combined blender-<version>.sha256 per release,
  # sha256sum format, a line per platform archive. A zero from a
  # single source is rule 3b's zero with no denominator, so this
  # tries both and prints how many it tried.
  #
  # THE COMBINED FILE MUST BE MATCHED BY FILENAME, never by "the
  # first 64 hex characters in the body" - that would take the
  # linux tarball's hash and compare it against the windows zip,
  # which reads as a MISMATCH and stops a perfectly good download.
  # Extracted as a function so the parse can be tested where the
  # tests run: tools/test-blender-hash-parse.py pulls THIS EXACT
  # TEXT out of this file with ps-check's own step extractor and
  # runs it against six fixtures, three accepting and three
  # rejecting. Renaming this function or this step makes that test
  # fail loudly rather than quietly cover nothing.
  function Get-PublishedHash([string]$body, [string]$wantFile) {
    if (-not $body) { return "" }
    if ($body -match [regex]::Escape($wantFile)) {
      foreach ($ln in ($body -split "`n")) {
        if ($ln.Contains($wantFile)) {
          $m1 = [regex]::Match($ln, '[0-9a-fA-F]{64}')
          if ($m1.Success) { return $m1.Value.ToLower() }
        }
      }
      return ""
    }
    # A per-file .sha256 with no name in it: a bare hash on its own
    # line. Anchored, so a stray 64-hex run inside an HTML error
    # page cannot pass for a published hash.
    $m2 = [regex]::Match($body, '(?m)^\s*([0-9a-fA-F]{64})\s*$')
    if ($m2.Success) { return $m2.Groups[1].Value.ToLower() }
    return ""
  }

  $published = ""
  $hashSource = "none"
  $hashTried = 0
  foreach ($hu in @("$url.sha256", ($lineUrl + "blender-$ver.sha256"))) {
    if ($published) { break }
    $hashTried++
    try {
      $hr = Invoke-WebRequest -Uri $hu -UseBasicParsing -TimeoutSec 60
      $hit = Get-PublishedHash "$($hr.Content)" $file
      if ($hit) { $published = $hit; $hashSource = $hu }
    } catch { }
  }
  $actual = (Get-FileHash -Path $zip -Algorithm SHA256).Hash.ToLower()
  $script:L += "checksumSourcesTried=$hashTried"
  if ($published -and $published -eq $actual) {
    $script:L += "checksum=match sha256=$actual"
    $script:L += "checksumSource=$hashSource"
  } elseif ($published) {
    $script:L += "checksum=MISMATCH published=$published actual=$actual"
    $script:L += "checksumSource=$hashSource"
    $script:L += "STOPPING: refusing to unpack a file that does not match its published hash."
    Finish "failed"; exit 1
  } else {
    $script:L += "checksum=not-published sha256=$actual"
    $script:L += "checksumSource=none"
    $script:L += "note: neither $url.sha256 nor $($lineUrl)blender-$ver.sha256 gave a hash for $file, so the download is unverified. The hash above is what arrived, not what upstream says."
  }

  # ONE EXTRACTOR, AND WHICH ONE RAN IS PRINTED. tar.exe in System32
  # is bsdtar and reads zip; the Windows build workflow already
  # unpacks python with it on this machine, so it is the tested-here
  # path. Expand-Archive is the fallback for a Windows without it
  # and ANNOUNCES ITSELF when it fires, because a fallback nobody is
  # told about is a fallback nobody can debug.
  $tarExe = Join-Path $env:SystemRoot "System32\tar.exe"
  $t0 = Get-Date
  $extractOk = $false
  if (Test-Path $tarExe) {
    $script:L += "extractTool=tar.exe"
    & $tarExe -x -f "$zip" -C "$dest"
    $rc = $LASTEXITCODE
    $script:L += "extractExit=$rc"
    $extractOk = ($rc -eq 0)
  } else {
    $script:L += "extractTool=Expand-Archive"
    $script:L += "note: FALLBACK FIRED - there is no tar.exe at $tarExe, so the slower managed unpacker ran instead."
    try { Expand-Archive -LiteralPath $zip -DestinationPath $dest -Force -ErrorAction Stop; $extractOk = $true }
    catch { $script:L += "EXTRACT FAILED: $($_.Exception.Message)" }
    $script:L += "extractExit=$(if ($extractOk) { '0' } else { '1' })"
  }
  $script:L += "extractMinutes=$([math]::Round(((Get-Date) - $t0).TotalMinutes, 1))"

  # THE DENOMINATOR. An exit code of 0 over an empty destination is
  # exactly what a truncated archive looks like, so "extracted" ships
  # the count of files that are actually there.
  #
  # AND THE EXE IS FOUND, NEVER ASSUMED. Blender release zips carry
  # a top-level blender-<ver>-windows-x64/ folder, so the binary may
  # sit one level deeper than $dest. Nothing here renames or moves
  # anything to make a guess come true: the tree is searched and the
  # resolved path is printed. The consumer searches recursively too,
  # so either layout is findable.
  $filesOut = @(Get-ChildItem -Path $dest -Recurse -File -ErrorAction SilentlyContinue)
  $script:L += "extractedFiles=$($filesOut.Count)"
  $exeItem = @($filesOut | Where-Object { $_.Name -eq "blender.exe" } | Select-Object -First 1)
  if ($exeItem.Count -gt 0) {
    $script:L += "blenderExeInExtract=$(Tilde $exeItem[0].FullName)"
  } else {
    $script:L += "blenderExeInExtract=none"
    $script:L += "note: the archive unpacked but there is no blender.exe anywhere under $dest, so either the wrong file was fetched or the unpack was partial."
    $script:L += "note: the named suspect for a partial unpack here is PATH LENGTH. $dest is 30-odd characters, the zip adds its own blender-<ver>-windows-x64 folder on top, and Blender carries a python tree whose deepest files run to about 200. If extractExit is non-zero or extractedFiles looks short, shorten the root before suspecting the download."
  }
  $script:L += "extractReportedOk=$(if ($extractOk -and $exeItem.Count -gt 0) { 'yes' } else { 'no' })"
}

# VERIFY BY RUNNING IT, on BOTH paths - an exit code is not evidence
# and neither is a file existing. The required set is named and
# counted so "found it and it runs" cannot read like "found a file".
$required = 2
$ok = 0
$path = Get-BlenderPath
if ($path) {
  $ok++
  $script:L += "verified: meshgen's own probe finds blender.exe, so the unpacked copy landed where the consumer looks."
  $script:L += "blenderPath=$(Tilde $path)"
  $script:L += "the same path with its real spaces: $path"
  $verLine = ""
  try {
    $o = & $path --version 2>&1
    foreach ($ln in @($o)) { if ("$ln".Trim() -ne "") { $verLine = "$ln".Trim(); break } }
  } catch { $script:L += "running it threw: $($_.Exception.Message)" }
  if ($verLine) {
    $script:L += "its own first line: $verLine"
    # A line came back is not the same fact as a VERSION came back:
    # a stderr record redirected in here would also be a line. The
    # requirement is met only when the thing names its version.
    $mv = [regex]::Match($verLine, '(\d+\.\d+(\.\d+)?)')
    if ($mv.Success) {
      $ok++
      $script:L += "verified: it RAN and reported its version."
      $script:L += "blenderVersion=$($mv.Groups[1].Value)"
    } else {
      $script:L += "NOT VERIFIED: it printed something, but no version number was in it."
      $script:L += "blenderVersion=unparsed"
    }
  } else {
    $script:L += "NOT VERIFIED: blender.exe is on disk but --version printed nothing at all."
    $script:L += "blenderVersion=none"
  }
} else {
  $script:L += "NOT VERIFIED: after this run meshgen's probe still finds no blender.exe."
  $script:L += "blenderPath=none"
  $script:L += "blenderVersion=none"
}
$onPath = ""
try { $onPath = (& where.exe blender.exe 2>$null | Select-Object -First 1) } catch { }
$script:L += "onPath=$(if ($onPath) { 'yes' } else { 'no' })"
$script:L += "note: PATH is not a requirement. probe-tools.ps1 searches C:\LedgerTools\blender FIRST, then Program Files\Blender Foundation, Steam and WindowsApps, and the LedgerTools branch is the one an unpacked copy is found by. That search list was extended for this step; without that edit an extracted Blender would be invisible to meshgen and this whole step would land nothing. Nothing here edits the machine PATH; that global belongs to the runner bootstrap."
$script:L += "probeJsonWritten=$script:probeWrote"
$script:L += "verifiedRequirements=$ok/$required"

if ($ok -eq $required) {
  if ($before) { $script:L += "DONE: Blender was already on this machine and it runs. Nothing changed."; Finish "already-present" }
  else { $script:L += "DONE: Blender was unpacked by THIS run and it runs."; Finish "extracted" }
  exit 0
}
$script:L += "meshgen's local backend will still refuse: $($required - $ok) of $required requirement(s) unmet."
Finish "failed"
exit 1

