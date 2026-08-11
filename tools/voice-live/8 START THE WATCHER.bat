@echo off
setlocal
title LEDGER - watcher
REM ===================================================================
REM  THE ONLY BAT YOU NEED. Double-click it and leave the window open.
REM
REM  WHAT CHANGED, AND WHY THE LAST FEW DAYS WERE LIKE THAT.
REM
REM  This machine used to commit its results onto the same branch I write
REM  code to. Two authors on one branch means every job could end in a
REM  divergence, a divergence needed a rebase, and a rebase needed a clean
REM  folder and an unlocked file and a rule for conflicts. Every failure
REM  you have seen came from that one decision, not from the scripts that
REM  kept trying to paper over it.
REM
REM  So this machine is not an author any more. It READS my branch and
REM  never merges anything: it makes its folder identical to the branch,
REM  which works from ANY state it could be in - half-finished rebase,
REM  stranded commit, diverged, detached. And it WRITES its answers to a
REM  branch nobody else touches, so a push can never be refused and can
REM  never destroy anything.
REM
REM  Nothing left to reconcile, so nothing left to go wrong that way, and
REM  no repair script to run when it does.
REM
REM  Close the window to stop it. Nothing is left running.
REM ===================================================================

REM RUN FROM A COPY. Matching the branch can rewrite this very file while
REM cmd.exe is still reading it by byte offset - which once made a script
REM print the tail of its own replacement.
if /i "%~1"=="--fromtemp" goto :begin
copy /y "%~f0" "%TEMP%\ledger-watch.bat" >nul
"%TEMP%\ledger-watch.bat" --fromtemp
exit /b %errorlevel%
:begin

set "REPO=%USERPROFILE%\wc26-picks"
set "BRANCH=claude/game-dev-ai-automation-2h67ix"
set "ENVDIR=%REPO%\tools\voice-live\env-export"
set "SAFE=%TEMP%\ledger-env-backup"
set "RESCUE=%USERPROFILE%\ledger-rescued"

echo.
echo  LEDGER - watcher
echo  ================
echo.
if not exist "%REPO%\.git" goto :norepo
cd /d "%REPO%"

REM ---- COPY ANYTHING THIS MACHINE MADE, SOMEWHERE GIT CANNOT REACH.
REM ---- Look before you destroy: a cancelled job once deleted 24 clips
REM ---- Jafar had already listened to, and reported success.
mkdir "%RESCUE%" >nul 2>&1
copy /y "game-design\pc-jobs\result.txt" "%RESCUE%\" >nul 2>&1
copy /y "game-design\voice-live\*.txt" "%RESCUE%\" >nul 2>&1
copy /y "game-design\voice-live\*.wav" "%RESCUE%\" >nul 2>&1

REM ---- MOVE THE WHOLE ENVIRONMENT OUT OF GIT'S WAY IF GIT IS TRACKING IT.
REM
REM  An old commit on this machine had the entire virtual environment
REM  committed by accident, so matching the branch DELETED it - a hundred
REM  thousand files. The first version of this guarded that by copying the
REM  launcher and the .exe files aside, which protects the cheap half of a
REM  folder and reads as a backup. It restored a launcher into a directory
REM  the reset had just removed, so it did not even do that.
REM
REM  A rename is instant, complete, and cannot half-work. Only done when
REM  git is actually tracking the folder, so the normal case pays nothing.
if exist "%ENVDIR%" (
  git --no-pager ls-files --error-unmatch "tools/voice-live/env-export" >nul 2>&1
  if not errorlevel 1 (
    echo  The environment is tracked by an old commit - moving it aside first.
    if exist "%SAFE%" rmdir /s /q "%SAFE%" >nul 2>&1
    move "%ENVDIR%" "%SAFE%" >nul 2>&1
  )
)

echo  Matching the branch...
REM  Any half-finished operation, ended. These fail harmlessly when there
REM  is nothing to end, and one of them left this machine unable to do
REM  anything at all for an afternoon.
git --no-pager rebase --abort >nul 2>&1
git --no-pager merge --abort >nul 2>&1
git --no-pager cherry-pick --abort >nul 2>&1

git --no-pager fetch origin %BRANCH%
if errorlevel 1 goto :nonet
REM  A DISCARD, NOT A MERGE. Nothing in this folder is worth keeping:
REM  results are published separately, and untracked files - the Python
REM  environment, the exported graphs - are not touched by this at all.
git --no-pager reset --hard FETCH_HEAD
if errorlevel 1 goto :noreset

REM  And put it back, whole. It is untracked from here on - the project
REM  ignores this path - so no later sync will look at it again.
if exist "%SAFE%" (
  if not exist "%ENVDIR%" move "%SAFE%" "%ENVDIR%" >nul 2>&1
)

if not exist "%ENVDIR%\Scripts\python.exe" goto :noenv
echo  Up to date. Watching for jobs - leave this window open.
echo.
"%ENVDIR%\Scripts\python.exe" tools\pc-watcher.py
echo.
echo  The watcher stopped. Close this window, or run this bat again.
pause
exit /b 0

:norepo
echo  No project at %REPO%
echo.
pause & exit /b 1

:nonet
echo.
echo  Could not reach GitHub. Nothing has been changed. Check the
echo  connection and run this again.
echo.
pause & exit /b 1

:noreset
echo.
echo  Could not match the branch, which should not be possible from any
echo  state. Send me this window.
echo.
pause & exit /b 1

:noenv
echo.
echo  The Python environment is not there. Run
echo  "1 RESTORE THE ENVIRONMENT.bat" first - it takes it back out of
echo  git's history in a few seconds, and tells you if it has to be
echo  rebuilt instead.
echo.
pause & exit /b 1
