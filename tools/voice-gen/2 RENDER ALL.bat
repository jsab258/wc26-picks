@echo off
setlocal
title LEDGER - render the bark bank
REM ===================================================================
REM  LEDGER 17.2, step 2 of 2. Run this AFTER "1 RATE TEST.bat", once
REM  you are happy the voices sound right.
REM
REM  It renders the 336 bark lines and pushes them, which is the step
REM  the Mixamo drop originally missed - the clips sat finished on one
REM  machine and the project never saw them.
REM
REM  SAFE TO INTERRUPT. It skips what is already rendered, so closing
REM  the window and running it again picks up where it stopped. It
REM  never deletes anything.
REM ===================================================================

REM ---- RUN FROM A COPY, same reason as step 1: this pulls -----------
if /i "%~1"=="--fromtemp" goto :begin
copy /y "%~f0" "%TEMP%\ledger-renderall.bat" >nul
"%TEMP%\ledger-renderall.bat" --fromtemp
exit /b %errorlevel%
:begin

set "REPO=%USERPROFILE%\wc26-picks"
set "TOOL=%REPO%\tools\voice-gen"
set "BRANCH=claude/game-dev-ai-automation-2h67ix"

if not exist "%REPO%\.git" goto :norepo

echo.
echo  Updating...
pushd "%REPO%"
git pull origin "%BRANCH%"
if errorlevel 1 goto :nopull
popd

cd /d "%TOOL%"
if not exist "env\Scripts\python.exe" goto :noenv
set "PY=%TOOL%\env\Scripts\python.exe"

echo.
"%PY%" ledger_voice_gen.py --plan
echo.
echo  ------------------------------------------------------------------
echo   ABOUT TEN HOURS. Every bark has to exist in all six street voices,
echo   because the game picks a walker's voice from WHO THEY ARE, not from
echo   the line - so a line your voice never recorded is a walker who says
echo   nothing. The 335 already done are kept; the rest is the overnight.
echo.
echo   Safe to leave. It saves its place every 25 clips, so closing the
echo   window or losing power costs you 25 clips, not the night.
echo.
echo   Close this window now if the numbers look wrong.
echo  ------------------------------------------------------------------
pause

"%PY%" ledger_voice_gen.py --all
if errorlevel 2 goto :nomodel
if errorlevel 1 goto :failed

echo.
echo  Rendered. Pushing...
REM  The same tested push the Mixamo drop and the voice installer use,
REM  parameterised by environment because %1 is already taken by its
REM  own TEMP-relaunch flag.
set "LEDGER_PUSH_PATH=ledger/Assets/StreamingAssets/Audio/Voice"
set "LEDGER_PUSH_MSG=Bark bank rendered: the street has a voice"
call "%REPO%\tools\mixamo-pick\PUSH.bat"
set "LEDGER_PUSH_PATH="
set "LEDGER_PUSH_MSG="
exit /b %errorlevel%

:norepo
echo.
echo  No project at %REPO%
echo.
pause & exit /b 1

:nopull
popd
echo.
echo  The PULL failed, so nothing was rendered. The reason is above.
echo.
pause & exit /b 1

:noenv
echo.
echo  No environment yet - run "1 RATE TEST.bat" first. It builds
echo  everything this needs and tells you whether the voices are right
echo  before you commit a few hours to them.
echo.
pause & exit /b 1

:nomodel
echo.
echo  chatterbox did not load, so nothing was rendered and nothing was
echo  pushed. The reason is above.
echo.
pause & exit /b 2

:failed
echo.
echo  The render FAILED - the reason is above, and NOTHING was pushed.
echo  Whatever did render is still on disk; running this again resumes
echo  from there rather than starting over.
echo.
pause & exit /b 1
