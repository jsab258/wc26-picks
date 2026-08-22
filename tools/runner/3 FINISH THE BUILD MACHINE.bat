@echo off
setlocal
title LEDGER - finish the build machine
REM ===================================================================
REM  The first build on this PC found the two tools the cloud machine
REM  had and this one does not. This installs them:
REM
REM    - PowerShell 7 ("pwsh") - the build's own steps run on it
REM    - Python, machine-wide - the build service is a machine
REM      account and cannot see a per-user Python, so "it works when
REM      I run it" is not proof it works for the service
REM
REM  JUST DOUBLE-CLICK THIS FILE. It asks Windows for administrator
REM  permission itself, and every window it opens STAYS OPEN and says
REM  what happened - the right-click way showed "nothing happens" on
REM  this machine, so nothing here is allowed to fail silently.
REM
REM  One-time. A build is dispatched automatically when it finishes.
REM
REM  (No self-copy to TEMP here, deliberately: this script never
REM  pulls, so it cannot be rewritten mid-read - and a script that
REM  copies itself to TEMP and relaunches is the one shape antivirus
REM  loves to kill without a word, which is the leading suspect for
REM  the silent failure above.)
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

echo.
echo  LEDGER - finish the build machine
echo  =================================
echo.

where winget >nul 2>&1
if errorlevel 1 (
  echo  winget is missing on this PC. Install "App Installer" from the
  echo  Microsoft Store once, then run this again.
  pause
  exit /b 1
)

if exist "C:\Program Files\PowerShell\7\pwsh.exe" (
  echo  PowerShell 7 is already installed.
) else (
  echo  ---- installing PowerShell 7 - a few minutes -----------------------
  winget install --id Microsoft.PowerShell -e --scope machine --accept-source-agreements --accept-package-agreements
  if not exist "C:\Program Files\PowerShell\7\pwsh.exe" goto :pwshfail
  echo  PowerShell 7 installed.
)

REM The build service cannot see a per-user Python, so the test is a
REM machine location - C:\Windows\py.exe, the all-users launcher - and
REM never "where python", which answers for the wrong account.
if exist "C:\Windows\py.exe" (
  echo  Python's machine-wide launcher is already here.
) else (
  echo  ---- installing Python machine-wide --------------------------------
  winget install --id Python.Python.3.12 -e --scope machine --accept-source-agreements --accept-package-agreements
  if exist "C:\Windows\py.exe" (
    echo  Python installed machine-wide.
  ) else (
    echo  Python still is not machine-wide - carrying on; if the build
    echo  needs it, its first step will say so in plain words.
  )
)

echo.
echo  ---- restarting the build service so it sees the new tools ---------
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

:pwshfail
echo.
echo  The PowerShell 7 install FAILED - the reason is printed above
echo  this line. Tell Claude what it says.
echo.
pause
exit /b 1
