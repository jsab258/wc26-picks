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

title LEDGER - get the latest from Claude
REM ===================================================================
REM  ONE CLICK: pulls everything Claude has pushed since you last
REM  looked - tools, scripts, docs - and says what arrived.
REM
REM  RUN FROM A COPY, and for this script it is not a nicety: a pull
REM  can rewrite THIS FILE while cmd.exe is still reading it by byte
REM  offset, which has produced half-a-URL error messages from other
REM  scripts on this machine.
REM ===================================================================
if /i "%~1"=="--fromtemp" goto :begin
copy /y "%~f0" "%TEMP%\ledger-update.bat" >nul
if not exist "%TEMP%\ledger-update.bat" (
  echo  Could not stage a working copy in %TEMP% - antivirus may have
  echo  blocked it. Tell Claude what this window says.
  pause & exit /b 1
)
"%TEMP%\ledger-update.bat" --fromtemp
REM Only reached when the working copy failed to START - on success the
REM line above transfers control and never returns. A window that closes
REM before it can speak is the one failure a launcher must not have.
echo  The working copy would not start - antivirus may have blocked it.
echo  Tell Claude what this window says.
pause
exit /b 1
:begin

set "REPO=%USERPROFILE%\wc26-picks"
set "BRANCH=claude/game-dev-ai-automation-2h67ix"

if not exist "%REPO%\.git" (
  echo  No project at %REPO%
  pause & exit /b 1
)
cd /d "%REPO%"

echo.
echo  LEDGER - get the latest from Claude
echo  ===================================
echo.
REM  AN UNFINISHED MERGE BLOCKS EVERY PULL AFTER IT, AND SAYS SO IN
REM  GIT'S WORDS RATHER THAN ANYONE'S. 26 Aug: a pull left MERGE_HEAD
REM  behind, and from then on this script failed with "You have not
REM  concluded your merge" — a sentence that names the state without
REM  naming the fix, so it read as "the pull is broken".
REM  LOOK BEFORE ABORTING (rule 5): what is half-merged is printed
REM  first, then aborted, then said. `merge --abort` restores the
REM  pre-merge state and does not touch untracked files, so generated
REM  pictures and harvested clips are never at risk.
if exist ".git\MERGE_HEAD" (
  echo  An earlier pull stopped half-way and has been blocking every
  echo  pull since. What was in the way:
  echo  ------------------------------------
  git --no-pager diff --name-only --diff-filter=U
  echo  ------------------------------------
  git merge --abort
  if errorlevel 1 (
    echo  Could not undo it automatically. Tell Claude what this says.
    pause & exit /b 1
  )
  echo  Undone - back to where you were before that pull. Carrying on.
  echo.
)

git fetch origin "%BRANCH%"
if errorlevel 1 goto :fail

for /f %%c in ('git rev-list --count HEAD..origin/%BRANCH%') do set BEHIND=%%c
if "%BEHIND%"=="0" (
  echo  Already up to date - nothing new since your last pull.
  echo.
  pause & exit /b 0
)

echo  %BEHIND% new change(s). What arrived:
echo  ------------------------------------
git --no-pager log --oneline HEAD..origin/%BRANCH% -15
echo  ------------------------------------
echo.
git pull origin "%BRANCH%"
if errorlevel 1 goto :fail

echo.
echo  DONE - everything is current.
echo.
pause
exit /b 0

:fail
echo.
echo  The pull FAILED - the reason is above. The commonest cause is
echo  local edits in the way: tell Claude what it printed.
echo.
pause & exit /b 1
