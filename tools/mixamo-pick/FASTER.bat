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

title LEDGER - speed the harvest up
cd /d "%~dp0"

REM ===================================================================
REM  RUN FROM A COPY, ALWAYS. This script does a git pull, and the pull
REM  can rewrite THIS FILE while cmd.exe is still reading it.
REM
REM  cmd re-reads a batch file from disk line by line, by BYTE OFFSET.
REM  Rewrite the file mid-run and it carries on at the same offset in
REM  the new bytes - landing mid-word, mid-block, anywhere. That is
REM  exactly what happened: a pull rewrote 120 lines of this file and
REM  execution resumed inside a message about installing Python,
REM  printing 'nloads' is not recognized - the tail of a URL.
REM
REM  So: copy myself to TEMP and re-launch from there. git cannot touch
REM  a file outside the repository, and the copy's bytes are frozen for
REM  the life of the run.
REM ===================================================================
if /i "%~1"=="--fromtemp" goto :begin
copy /y "%~f0" "%TEMP%\ledger-%~n0.bat" >nul
"%TEMP%\ledger-%~n0.bat" --fromtemp
exit /b %errorlevel%
:begin



REM ===================================================================
REM  Cuts the harvest from ~9 hours to ~1.8 by doing two things:
REM
REM  1. ONE CHARACTER instead of two. Mixamo rigs import into Unity as
REM     Humanoid and Humanoid clips retarget onto any humanoid avatar,
REM     so X Bot's animations drive the female body too. Y Bot's 2,400
REM     copies are the same motions on slightly different bone lengths.
REM     We need both MESHES; we do not need both sets of CLIPS.
REM
REM  2. FIVE THREADS instead of two. Two was me being a polite guest.
REM     Five is the tool's own default.
REM
REM  Stop the running harvest first (close its window). Nothing is lost -
REM  it keeps a state.json and skips everything already downloaded.
REM ===================================================================

set "MH=%USERPROFILE%\ledger-mixamo\MixamoHarvester"
set "XBOT=2dee24f8-3b49-48af-b735-c6377509eaac"
set "BRANCH=claude/game-dev-ai-automation-2h67ix"
set "REPO=%USERPROFILE%\wc26-picks"

echo.
echo  Speeding up the harvest
echo  =======================
echo.

if not exist "%MH%\mixamo_harvester.py" (
  echo  No harvester at %MH%
  echo  Run SETUP.bat or GO.bat first.
  pause & exit /b 1
)

REM  PULL FIRST. GO.bat commits the clips and pushes them at the end,
REM  and a push from a copy that is behind the remote is REJECTED - so a
REM  two-hour harvest would end in an error that has nothing to do with
REM  the harvest. Cheapest possible insurance, taken here because this is
REM  what runs first.
echo  [0/2] Updating the project...
pushd "%REPO%"
git pull origin "%BRANCH%"
if errorlevel 1 echo  Pull failed - the push at the end may be refused. Tell me if so.
popd

echo  [1/2] Pinning to X Bot only...
echo ["%XBOT%"]> "%MH%\characters.json"
findstr /C:"%XBOT%" "%MH%\characters.json" >nul || (
  echo  Could not write characters.json - tell me.
  pause & exit /b 1
)
echo        ...confirmed.

echo  [2/2] Threads to 5...
>"%MH%\threads.txt" echo 5
powershell -NoProfile -Command ^
  "$p='%MH%\mixamo_harvester.py'; $t=[IO.File]::ReadAllText($p); $t=$t -replace 'MAX_THREADS\s*=\s*\d+','MAX_THREADS = 5'; [IO.File]::WriteAllText($p,$t)"
findstr /C:"MAX_THREADS = 5" "%MH%\mixamo_harvester.py" >nul || (
  echo  Could not set the thread count - tell me.
  pause & exit /b 1
)
echo        ...confirmed.

echo.
echo  ------------------------------------------------------------
echo   Done. What to run next depends on where you are:
echo.
echo   HARVEST NOT FINISHED YET  ->  GO.bat
echo       picks up where it left off, ~2 hours from cold.
echo.
echo   HARVEST ALREADY FINISHED  ->  PUSH.bat
echo       do NOT run GO.bat again. It restarts the whole flow and
echo       re-walks 2,500 clips to skip nearly all of them. The clips
echo       are already picked; only the push is outstanding.
echo.
echo   The 5 threads are remembered in threads.txt, so re-running
echo   GO.bat keeps the setting rather than resetting it.
echo  ------------------------------------------------------------
pause
