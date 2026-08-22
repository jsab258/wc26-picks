@echo off
setlocal
title LEDGER - finish the build machine
REM ===================================================================
REM  The first build on this PC found the two tools the cloud machine
REM  had and this one does not: PowerShell 7 ("pwsh") and a Python the
REM  build service can see. This puts both in place.
REM
REM  NO INSTALLERS. The PowerShell installer died at 92% with "Access
REM  is denied" on this PC (22 Aug) - Windows' installer service is
REM  blocked by something. Both tools also ship as plain zips, so this
REM  script only downloads and unpacks files, verifies each landing,
REM  and falls back to C:\LedgerTools when Program Files refuses. The
REM  build probes every landing zone by absolute path.
REM
REM  JUST DOUBLE-CLICK THIS FILE. It asks Windows for administrator
REM  permission itself, and every window STAYS OPEN and says what
REM  happened. One-time; a build is dispatched when it finishes.
REM ===================================================================

net session >nul 2>&1
if not errorlevel 1 goto :main

if /i "%~1"=="--elevated" (
  echo.
  echo  Windows opened this window WITHOUT administrator rights.
  echo  Something on this machine is refusing the elevation.
  echo  Tell Claude "no admin" in the chat.
  echo.
  pause
  exit /b 1
)

echo.
echo  Asking Windows for administrator permission - a prompt should
echo  appear now. Click Yes.
echo.
powershell -NoProfile -Command "try { Start-Process cmd.exe -ArgumentList '/k','\"%~f0\" --elevated' -Verb RunAs -ErrorAction Stop } catch { exit 1 }"
if errorlevel 1 (
  echo  The permission prompt was refused or blocked.
) else (
  echo  If a new LEDGER window appeared, follow it - this one is done.
)
echo.
echo  If NO new window appeared, do it by hand:
echo    1. press the Windows key and type: cmd
echo    2. right-click "Command Prompt", choose "Run as administrator"
echo    3. paste this line into it and press Enter:
echo.
echo    "%~f0" --elevated
echo.
pause
exit /b 0

:main
set "REPO=%USERPROFILE%\wc26-picks"
set "BRANCH=claude/game-dev-ai-automation-2h67ix"
set "TOOLS=C:\LedgerTools"

echo.
echo  LEDGER - finish the build machine
echo  =================================
echo.

REM ---- PowerShell 7: plain zip, no installer -------------------------
set "PWSHDIR="
if exist "C:\Program Files\PowerShell\7\pwsh.exe" set "PWSHDIR=C:\Program Files\PowerShell\7"
if not defined PWSHDIR if exist "%TOOLS%\pwsh7\pwsh.exe" set "PWSHDIR=%TOOLS%\pwsh7"
if defined PWSHDIR (
  echo  PowerShell 7 is already at %PWSHDIR%
  goto :python
)

echo  ---- fetching PowerShell 7 as a plain zip, about 110 MB ------------
curl.exe -L --fail --retry 2 --retry-delay 3 -o "%TEMP%\ledger-pwsh7.zip" "https://github.com/PowerShell/PowerShell/releases/download/v7.4.6/PowerShell-7.4.6-win-x64.zip"
if errorlevel 1 (
  echo.
  echo  The download FAILED - the reason is above. Is the internet up?
  echo  Tell Claude what it says.
  pause
  exit /b 1
)

echo  ---- unpacking (a minute or two) -----------------------------------
powershell -NoProfile -Command "Expand-Archive -LiteralPath '%TEMP%\ledger-pwsh7.zip' -DestinationPath 'C:\Program Files\PowerShell\7' -Force"
if exist "C:\Program Files\PowerShell\7\pwsh.exe" set "PWSHDIR=C:\Program Files\PowerShell\7"
if not defined PWSHDIR (
  echo  Program Files would not take it - trying %TOOLS%\pwsh7 instead.
  powershell -NoProfile -Command "Expand-Archive -LiteralPath '%TEMP%\ledger-pwsh7.zip' -DestinationPath '%TOOLS%\pwsh7' -Force"
  if exist "%TOOLS%\pwsh7\pwsh.exe" set "PWSHDIR=%TOOLS%\pwsh7"
)
if not defined PWSHDIR (
  echo.
  echo  Neither folder would take the files - antivirus is blocking
  echo  writes. Tell Claude, and say which antivirus this PC runs.
  pause
  exit /b 1
)
"%PWSHDIR%\pwsh.exe" -NoProfile -Command "'PowerShell ' + $PSVersionTable.PSVersion.ToString() + ' unpacked and working.'"

:python
REM ---- Python: the build service is a machine account and cannot see
REM ---- a per-user Python, so machine locations only - and the zip
REM ---- build needs no installer either. The build's own scripts use
REM ---- nothing outside the standard library, which the zip carries.
if exist "C:\Windows\py.exe" (
  echo  Python's machine-wide launcher is already here.
  goto :service
)
if exist "%TOOLS%\python312\python.exe" (
  echo  Python is already at %TOOLS%\python312
  goto :service
)

echo  ---- fetching Python as a plain zip, about 11 MB -------------------
curl.exe -L --fail --retry 2 --retry-delay 3 -o "%TEMP%\ledger-py312.zip" "https://www.python.org/ftp/python/3.12.8/python-3.12.8-embed-amd64.zip"
if errorlevel 1 (
  echo.
  echo  The download FAILED - the reason is above. Is the internet up?
  echo  Tell Claude what it says.
  pause
  exit /b 1
)
powershell -NoProfile -Command "Expand-Archive -LiteralPath '%TEMP%\ledger-py312.zip' -DestinationPath '%TOOLS%\python312' -Force"
if not exist "%TOOLS%\python312\python.exe" (
  echo.
  echo  Could not unpack Python - antivirus is blocking writes.
  echo  Tell Claude, and say which antivirus this PC runs.
  pause
  exit /b 1
)
"%TOOLS%\python312\python.exe" --version

:service
echo.
echo  ---- restarting the build service so it starts fresh ---------------
powershell -NoProfile -Command "$s = Get-Service 'actions.runner.*' -ErrorAction SilentlyContinue; if ($s) { $s | Restart-Service; 'runner service restarted' } else { 'NO runner service found - was bat 1 run on this PC?' }"

echo.
echo  ---- telling Claude to dispatch a fresh build ----------------------
if exist "%REPO%\.git" (
  pushd "%REPO%"
  > tools\runner\DEPS.txt echo pwsh and python present on %COMPUTERNAME% at %DATE% %TIME%
  git add tools\runner\DEPS.txt >nul 2>&1
  git commit -m "Build machine finished: pwsh and python in place" >nul 2>&1
  git push origin HEAD:%BRANCH% >nul 2>&1 && (
    echo   Sent - a build heads this way shortly.
  ) || (
    echo   Could not push the signal - tell Claude "deps installed" in the chat.
  )
  popd
) else (
  echo   No project folder at %REPO% from this account.
  echo   Tell Claude "deps installed" in the chat.
)

echo.
echo  DONE. This window can be closed.
echo.
pause
exit /b 0
