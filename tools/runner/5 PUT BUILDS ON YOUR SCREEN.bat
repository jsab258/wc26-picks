@echo off
setlocal
title LEDGER - put builds on your screen
REM ===================================================================
REM  THE LAST WALL, and the game itself reported it: the build service
REM  lives in an invisible Windows session with no display, so the
REM  game booted, asked for a 1280x720 window, got "DX11 could not
REM  switch resolution", and sat there until the timeout. A background
REM  service can compile; it cannot RENDER.
REM
REM  This moves the build agent out of the invisible service and into
REM  YOUR normal desktop session, where the real GPU and the real
REM  screen live - which is also the only place the game's frame rate
REM  can be measured honestly. After this:
REM
REM    - when a build runs, THE GAME WINDOW OPENS ON YOUR DESKTOP for
REM      a few minutes and closes itself. That is normal - let it be.
REM    - builds run while you are logged in (the PC can sit at your
REM      desktop; a screensaver is fine, but not signed out).
REM    - it starts itself again every time you log in.
REM
REM  JUST DOUBLE-CLICK THIS FILE. It asks for administrator permission
REM  itself (needed once, to remove the old service) and every window
REM  stays open and says what happened.
REM ===================================================================

net session >nul 2>&1
if not errorlevel 1 goto :main

if /i "%~1"=="--elevated" (
  echo.
  echo  Windows opened this window WITHOUT administrator rights.
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
set "RUNNERDIR=C:\actions-runner-ledger"

echo.
echo  LEDGER - put builds on your screen
echo  ==================================
echo.

if not exist "%RUNNERDIR%\run.cmd" (
  echo  No build agent at %RUNNERDIR% - was bat 1 run on this PC?
  pause
  exit /b 1
)

echo  ---- removing the invisible background service ---------------------
powershell -NoProfile -Command "$s = Get-Service 'actions.runner.*' -ErrorAction SilentlyContinue; if ($s) { $s | Stop-Service -Force; $s | ForEach-Object { sc.exe delete $_.Name }; 'service removed' } else { 'no service found - already removed' }"

echo.
echo  ---- starting the agent on your desktop, and at every logon --------
REM A tiny starter in the Startup folder relaunches it each login;
REM `start /min` keeps it out of the way in a minimised window. Closing
REM that window stops builds until next logon or another double-click
REM of this file (no admin needed for a restart - the service is gone).
> "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\LEDGER build agent.cmd" (
  echo @echo off
  echo start "LEDGER build agent" /min "%RUNNERDIR%\run.cmd"
)
start "LEDGER build agent" /min "%RUNNERDIR%\run.cmd"
echo  Agent started - look for "LEDGER build agent" in your taskbar.

echo.
echo  ---- telling Claude to dispatch a fresh build ----------------------
if exist "%REPO%\.git" (
  pushd "%REPO%"
  > tools\runner\DISPLAY.txt echo Build agent on the desktop of %COMPUTERNAME% at %DATE% %TIME%
  git add tools\runner\DISPLAY.txt >nul 2>&1
  git commit -m "Build agent moved onto the desktop session" >nul 2>&1
  git push origin HEAD:%BRANCH% >nul 2>&1 && (
    echo   Sent - a build heads this way shortly. The game window will
    echo   open by itself when it does; let it run.
  ) || (
    echo   Could not push the signal - tell Claude "on screen now" in the chat.
  )
  popd
) else (
  echo   No project folder at %REPO% from this account.
  echo   Tell Claude "on screen now" in the chat.
)

echo.
echo  DONE. This window can be closed.
echo.
pause
exit /b 0
