@echo off
setlocal
title LEDGER - speed the harvest up
cd /d "%~dp0"

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
for %%R in ("%~dp0..\..") do set "REPO=%%~fR"

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
echo   Done. Now double-click GO.bat again - it will pick up where
echo   it left off and should finish in around two hours.
echo.
echo   The 5 is remembered in threads.txt, so re-running GO.bat as
echo   often as you like will keep it rather than reset it.
echo  ------------------------------------------------------------
pause
