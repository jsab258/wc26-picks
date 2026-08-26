@echo off
setlocal
REM  GIT MUST NEVER OPEN AN EDITOR HERE. 26 Aug: a `git pull` that made a
REM  merge commit opened vim in Jafar's window, he closed it, and the
REM  half-finished merge blocked every pull afterwards - which then read
REM  as "the pull is broken" rather than "something is waiting for you".
REM  `true` is a program that exits 0 immediately, so git takes the default
REM  message and carries on. TWENTY-TWO .bat files ran `git pull` and NOT
REM  ONE guarded this: one idea, twenty-two implementations, in scripts
REM  whose entire purpose is that nobody is watching the window.
set "GIT_EDITOR=true"
set "GIT_MERGE_AUTOEDIT=no"

title LEDGER - update
cd /d "%~dp0"

REM ===================================================================
REM  RUN FROM A COPY. A pull can rewrite this file while cmd.exe is
REM  reading it by byte offset, which is how a script ended up printing
REM  'nloads' - the tail of a URL from its own replacement.
REM ===================================================================
if /i "%~1"=="--fromtemp" goto :begin
copy /y "%~f0" "%TEMP%\ledger-%~n0.bat" >nul
"%TEMP%\ledger-%~n0.bat" --fromtemp
exit /b %errorlevel%
:begin

REM ===================================================================
REM  JUST PULLS. Nothing else.
REM
REM  This exists because "you need to pull to get the thing that pulls"
REM  came up three times in one afternoon. SETUP.bat pulls but then
REM  launches a two-hour harvest; FASTER.bat pulls but also re-tunes the
REM  harvester; PUSH.bat pulls but also pushes. None of them is the
REM  answer to "I just want the newest files".
REM ===================================================================

set "REPO=%USERPROFILE%\wc26-picks"
set "BRANCH=claude/game-dev-ai-automation-2h67ix"

echo.
echo  LEDGER - update
echo  ===============
echo.
if not exist "%REPO%\.git" goto :norepo
pushd "%REPO%"
REM ---- REBASE RATHER THAN A BARE PULL.
REM
REM  A bare "git pull" refuses outright when the branch has moved on both
REM  sides - git will not guess how to reconcile them - so this failed on
REM  the one day it was most needed, with a message about merge strategies
REM  that says nothing about what to do. Rebasing puts anything made on
REM  this machine on top of the branch, which is what "update" means here.
git pull --rebase origin "%BRANCH%"
if errorlevel 1 goto :failed
REM ---- AND SAY IF SOMETHING IS STILL WAITING TO GO BACK. This bat only
REM ---- pulls, by design, so a commit made here is now up to date and
REM ---- still not on GitHub - which is exactly the state that leaves the
REM ---- watcher stuck. Named rather than left to be discovered.
set "AHEAD="
for /f "delims=" %%i in ('git log --oneline "FETCH_HEAD..HEAD" 2^>nul') do set "AHEAD=1"
popd
if defined AHEAD goto :ahead
echo.
echo  ------------------------------------------------------------
REM  IT PULLS THE WHOLE REPOSITORY, and this line used to say only
REM  "everything in tools\mixamo-pick is current" - true when this
REM  folder was the only one with scripts in it, and quietly wrong
REM  once voice-gen existed. Somebody looking for the newest voice
REM  tools would have read that as "this did not update them".
echo   Up to date - the whole project, not just this folder.
echo.
echo   The scripts you can double-click live in:
echo     tools\voice-gen      the bark voices  (start with "1 RATE TEST")
echo     tools\voice-fetch    picking reference voices
echo     tools\mixamo-pick    bodies and animations
echo  ------------------------------------------------------------
pause & exit /b 0

:ahead
echo.
echo  ------------------------------------------------------------
echo   Updated - but this machine has work that is NOT on GitHub yet.
echo   That is what leaves the watcher stuck saying "cannot
echo   fast-forward". Run this next:
echo.
echo     tools\voice-live\9 UNSTICK THE WATCHER.bat
echo  ------------------------------------------------------------
echo.
pause & exit /b 0

:norepo
echo  No project at %REPO% - run SETUP.bat first.
pause & exit /b 1

:failed
popd
echo.
echo  The pull failed - the reason is above. Send it to me.
pause & exit /b 1
