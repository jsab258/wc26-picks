@echo off
setlocal
title LEDGER - play the street
REM ===================================================================
REM  QUEUE 138 ITEM 1: A CHARACTER YOU CAN CONTROL IN THE TEXTURED
REM  STREET, WITH A CAMERA. Double-click this file. A window opens on
REM  your desktop with a person standing on Meridian's own street -
REM  WASD to walk, mouse to look. Close the game window (or press
REM  Alt+F4) when you are done; this window then finishes by itself.
REM
REM  THIS RUNS NO AUTOMATION AND NO GIT COMMAND. It launches the same
REM  packaged LedgerProbe.exe the CI workflow already builds, plainly,
REM  with no -LedgerVignette / -LedgerShot / -LedgerGoldenTest switch,
REM  which is what makes it playable rather than a screenshot run: see
REM  ue-probe/Source/LedgerProbe/Private/LedgerGameMode.cpp for the one
REM  place that decides what a bare launch gets.
REM
REM  WHERE THE BUILD LIVES IS NOT HARD-CODED, on purpose. The packaged
REM  exe is written by the self-hosted CI runner (ledger-pc) into ITS
REM  OWN checkout, which is a different folder from the one this
REM  Telegram-updated copy of the repo lives in, and the exact folder
REM  name GitHub Actions gives that checkout has never been measured
REM  from inside this container. So this searches every plausible root
REM  recursively for LedgerProbe.exe under a Binaries\Win64 folder -
REM  the same shape ledger-probe-unreal.yml's own build step already
REM  uses to tell the real binary apart from the archive-root launcher
REM  stub - and plays the newest one it finds. If it finds none, it
REM  says so and names every root it looked under.
REM ===================================================================

echo.
echo  LEDGER - play the street
echo  ========================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference = 'Continue';" ^
  "$roots = @(" ^
  "  'C:\actions-runner-ledger\_work\wc26-picks\wc26-picks\ue-probe\Packaged'," ^
  "  (Join-Path $env:USERPROFILE 'wc26-picks\ue-probe\Packaged')," ^
  "  'C:\actions-runner-ledger\_work'" ^
  ") | Select-Object -Unique;" ^
  "$found = @();" ^
  "foreach ($r in $roots) {" ^
  "  if (Test-Path $r) {" ^
  "    $found += Get-ChildItem -Path $r -Filter 'LedgerProbe.exe' -Recurse -ErrorAction SilentlyContinue |" ^
  "              Where-Object { $_.FullName -match '\\Binaries\\Win64\\' };" ^
  "  }" ^
  "}" ^
  "$found = $found | Sort-Object LastWriteTime -Descending;" ^
  "Write-Host ('roots searched: ' + $roots.Count + ', LedgerProbe.exe under Binaries\Win64 found: ' + $found.Count);" ^
  "if ($found.Count -eq 0) {" ^
  "  Write-Host '';" ^
  "  Write-Host 'NO PACKAGED BUILD FOUND. Roots searched:';" ^
  "  foreach ($r in $roots) { Write-Host ('  ' + $r + ' (exists: ' + (Test-Path $r) + ')') };" ^
  "  Write-Host '';" ^
  "  Write-Host 'Tell Claude: no build found for PLAY THE STREET, and name a root';" ^
  "  Write-Host 'that does exist on this PC, or dispatch the LEDGER Unreal probe workflow';" ^
  "  Write-Host 'first so there is a packaged build to play.';" ^
  "  exit 1;" ^
  "}" ^
  "$exe = $found[0];" ^
  "Write-Host ('playing: ' + $exe.FullName);" ^
  "Write-Host ('built:   ' + $exe.LastWriteTime);" ^
  "Write-Host '';" ^
  "Write-Host 'A window is opening now. WASD to walk, mouse to look.';" ^
  "Write-Host 'Close that window (or Alt+F4) when you are done.';" ^
  "Start-Process -FilePath $exe.FullName -ArgumentList @('-windowed','-ResX=1280','-ResY=720') -Wait;" ^
  "Write-Host '';" ^
  "Write-Host 'The game window closed.';" ^
  "exit 0"

echo.
echo  DONE. This window can be closed.
echo.
pause
exit /b 0
