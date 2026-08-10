@echo off
setlocal
title LEDGER - waiting for jobs
REM ===================================================================
REM  LEAVE THIS RUNNING AND I CAN START THINGS MYSELF.
REM
REM  Every measurement that needs your graphics card or the 4.5 GB of
REM  model files has to run on this machine, and until now the only way
REM  to start one was to ask you to double-click something. That costs
REM  a message and a wait each time, and twice today an answer arrived
REM  hours after it would have been useful.
REM
REM  This window checks the project every minute. When I leave a request
REM  in it, this runs the job and pushes the result back - the same way
REM  the reports already come to me.
REM
REM  IT CANNOT RUN ANYTHING I FEEL LIKE. The request names a job from a
REM  fixed list written into the code - "time a line", "export the
REM  graphs" - and that name is looked up, not executed. Nothing in a
REM  request can invent a new command.
REM
REM  It is also deliberately NOT the standard tool for this. That would
REM  be a GitHub runner, and on a public project a runner lets a
REM  stranger's pull request run code on your desktop. This has no such
REM  door: it only ever runs what is already committed to your branch.
REM
REM  Close the window to stop it. Nothing is left running.
REM ===================================================================

if defined LEDGER_WATCHER_FROMTEMP goto :begin
set "LEDGER_WATCHER_FROMTEMP=1"
copy /y "%~f0" "%TEMP%\ledger-watcher.bat" >nul
"%TEMP%\ledger-watcher.bat" %*
exit /b %errorlevel%
:begin

set "REPO=%USERPROFILE%\wc26-picks"
set "ENVDIR=%REPO%\tools\voice-live\env-export"
if not exist "%REPO%\.git" goto :norepo

echo.
echo  LEDGER - waiting for jobs
echo  =========================
echo.
echo  Leave this window open. It checks once a minute and is idle in
echo  between. Closing it stops everything.
echo.
pushd "%REPO%"
git pull origin claude/game-dev-ai-automation-2h67ix
if not exist "%ENVDIR%\Scripts\python.exe" goto :noenv
"%ENVDIR%\Scripts\python.exe" tools\pc-watcher.py
popd
pause
exit /b 0

:norepo
echo. & echo  No project at %REPO% & echo.
pause & exit /b 1

:noenv
popd
echo.
echo  The environment is not there yet. Run "2 TRY THE EXPORT.bat" first.
echo.
pause & exit /b 1
