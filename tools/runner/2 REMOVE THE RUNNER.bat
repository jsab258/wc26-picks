@echo off
setlocal
title LEDGER - move the builds back to the cloud
REM ===================================================================
REM  Undoes "1 SET UP THE BUILD RUNNER". Needs administrator rights
REM  (right-click, "Run as administrator") and one paste: GitHub shows
REM  a REMOVAL token on the runner's page.
REM
REM  Tell Claude afterwards, so the build workflow flips back to the
REM  cloud machine - otherwise builds queue forever waiting for a
REM  runner that no longer exists.
REM ===================================================================

net session >nul 2>&1
if errorlevel 1 (
  echo  Needs administrator rights - right-click, "Run as administrator".
  pause & exit /b 1
)

set "RUNNERDIR=C:\actions-runner-ledger"
if not exist "%RUNNERDIR%\.runner" (
  echo  No runner is configured here. Nothing to do.
  pause & exit /b 0
)

echo.
echo  Open this page, click the "ledger-pc" runner, choose Remove, and
echo  copy the token it shows:
echo.
echo    https://github.com/jsab258/wc26-picks/settings/actions/runners
echo.
set /p TOKEN="  paste the removal token here and press Enter: "
if "%TOKEN%"=="" ( echo  Nothing pasted - stopping. & pause & exit /b 1 )

cd /d "%RUNNERDIR%"
call config.cmd remove --token %TOKEN%
if errorlevel 1 (
  echo  Removal FAILED - the reason is above.
  pause & exit /b 1
)

echo.
echo  DONE. Tell Claude "runner removed" so builds go back to the cloud.
echo.
pause
exit /b 0
