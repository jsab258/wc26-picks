@echo off
setlocal
title LEDGER - re-pick the clips
cd /d "%~dp0"

REM ===================================================================
REM  RUN FROM A COPY. This script pulls, and a pull can rewrite THIS FILE
REM  while cmd.exe is still reading it by byte offset - which produced
REM  'nloads' is not recognized, the tail of a URL, from a script that had
REM  been replaced underneath itself mid-run.
REM ===================================================================
if /i "%~1"=="--fromtemp" goto :begin
copy /y "%~f0" "%TEMP%\ledger-%~n0.bat" >nul
"%TEMP%\ledger-%~n0.bat" --fromtemp
exit /b %errorlevel%
:begin

REM ===================================================================
REM  Re-runs the PICK against the harvest already on disk. No downloads,
REM  no token, seconds rather than hours.
REM
REM  Needed because the first pick ran against clip names I had guessed
REM  from memory. The harvest produced the real catalogue, the wants list
REM  was rebuilt from it, and this applies that: eleven more clips, and
REM  better answers for four that had settled for a substitute.
REM ===================================================================

set "MH=%USERPROFILE%\ledger-mixamo\MixamoHarvester"
set "REPO=%USERPROFILE%\wc26-picks"
set "SCRIPTS=%REPO%\tools\mixamo-pick"
set "BRANCH=claude/game-dev-ai-automation-2h67ix"

echo.
echo  LEDGER - re-picking the clips
echo  =============================
echo.

if not exist "%MH%\animations" goto :noharvest

echo  [1/3] Updating the project...
pushd "%REPO%"
git pull origin "%BRANCH%"
if errorlevel 1 echo  Pull failed - carrying on with what is here.
popd

echo  [2/3] Picking...
python "%SCRIPTS%\pick_animations.py" --harvest "%MH%\animations" --out "%REPO%\ledger\Assets\Characters"
if errorlevel 1 goto :pickfailed

echo  [3/3] Pushing...
call "%SCRIPTS%\PUSH.bat"
exit /b %errorlevel%

:noharvest
echo  No harvest at %MH%\animations
echo  Nothing to re-pick from. Run GO.bat first.
pause & exit /b 1

:pickfailed
echo  The pick failed - the reason is above. Send it to me.
pause & exit /b 1
