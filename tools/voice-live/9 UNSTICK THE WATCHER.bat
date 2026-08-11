@echo off
setlocal
title LEDGER - unstick the watcher
REM ===================================================================
REM  RUN THIS ONCE IF THE WATCHER IS REPEATING "cannot fast-forward".
REM
REM  What went wrong: when a job finished, the watcher committed its
REM  result and then tried to push. If anything had been pushed to the
REM  branch while the job was running - which is most of the time, since
REM  a job takes half an hour - the push was rejected and the commit was
REM  left sitting on this machine. Every check after that hit the same
REM  wall and printed the same line, once a minute, for ever.
REM
REM  This puts that commit on top of everything else and pushes it. It
REM  keeps the work; nothing is forced and nothing is thrown away. If
REM  the two sides genuinely conflict it stops and says so rather than
REM  picking a winner.
REM
REM  You do NOT need to restart the watcher afterwards. Once the branch
REM  is straight again it will notice within a minute, pick up the
REM  repaired version of itself, and carry on - including doing this
REM  repair on its own next time.
REM ===================================================================

set "REPO=%USERPROFILE%\wc26-picks"
set "BRANCH=claude/game-dev-ai-automation-2h67ix"

echo.
echo  LEDGER - unstick the watcher
echo  ============================
echo.

if not exist "%REPO%\.git" goto :norepo
pushd "%REPO%"

REM ---- NOTHING UNCOMMITTED, OR STOP. Replaying a commit with unsaved
REM ---- work in the folder is how this project once destroyed a Python
REM ---- environment. If there is anything here, it gets named, not
REM ---- swept aside.
set "DIRTY="
for /f "delims=" %%i in ('git status --porcelain') do set "DIRTY=1"
if defined DIRTY goto :dirty

echo  Fetching the branch...
git fetch origin %BRANCH%
if errorlevel 1 goto :nonet

REM What is here that the branch has not got? Printed BEFORE anything
REM moves, so you can see what is being rescued.
echo.
echo  Waiting to be pushed from this machine:
git log --oneline FETCH_HEAD..HEAD
echo.

echo  Replaying it on top of the branch...
git rebase FETCH_HEAD
if errorlevel 1 goto :conflict

echo.
echo  Pushing...
git push origin HEAD:%BRANCH%
if errorlevel 1 goto :nopush

REM ---- AND PROVE IT LANDED. A push can report success having sent
REM ---- nothing at all, which is a mistake this project has already
REM ---- made once and read as a working pipeline.
git fetch origin %BRANCH%
git merge-base --is-ancestor HEAD FETCH_HEAD
if errorlevel 1 goto :notlanded

popd
echo.
echo  DONE - the branch is straight and this machine's work is on it.
echo.
echo  Leave the watcher window as it is. Within a minute it will pick up
echo  the repaired version and carry on by itself.
echo.
pause
exit /b 0

:dirty
echo  STOPPED - there are unsaved changes in the project folder:
echo.
git status --short
echo.
echo  Nothing has been touched. Tell me what is in that list and I will
echo  say whether it matters.
popd
echo.
pause
exit /b 1

:conflict
echo.
echo  STOPPED - this machine's commit and the branch changed the same
echo  thing, so there is no safe automatic answer. Backing out cleanly.
git rebase --abort
echo.
echo  Nothing was forced and nothing was lost. Send me this window.
popd
echo.
pause
exit /b 1

:nonet
echo  STOPPED - could not reach GitHub. Nothing has been changed.
popd
echo.
pause
exit /b 1

:nopush
echo.
echo  STOPPED - the push was refused. Nothing was forced. Send me this
echo  window and I will read the reason.
popd
echo.
pause
exit /b 1

:notlanded
echo.
echo  STOPPED - the push reported success but the branch does not carry
echo  the commit. That is the one failure that used to read as working.
echo  Send me this window.
popd
echo.
pause
exit /b 1

:norepo
echo  No project at %REPO%
echo.
pause
exit /b 1
