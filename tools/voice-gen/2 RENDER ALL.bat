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
cd /d "%~dp0"

if not exist "env\Scripts\python.exe" (
  echo.
  echo  No environment yet - run "1 RATE TEST.bat" first. It builds
  echo  everything this needs and tells you whether the voices are right
  echo  before you commit a few hours to them.
  echo.
  pause & exit /b 1
)
set "PY=%~dp0env\Scripts\python.exe"

echo.
"%PY%" ledger_voice_gen.py --plan
echo.
echo  ------------------------------------------------------------------
echo   That is what will be rendered. Close this window now if the
echo   numbers look wrong.
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
set "LEDGER_PUSH_PATH=ledger/Assets/Resources/voice/barks"
set "LEDGER_PUSH_MSG=Bark bank rendered: the street has a voice"
call "%~dp0..\mixamo-pick\PUSH.bat"
set "LEDGER_PUSH_PATH="
set "LEDGER_PUSH_MSG="
exit /b %errorlevel%

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
