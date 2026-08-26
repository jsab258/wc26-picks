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

title LEDGER - can the cast speak live?
REM ===================================================================
REM  DO NOT RUN THIS WHILE THE BARKS ARE RENDERING.
REM
REM  Not a style note. The bark render is a two-hour-plus job holding
REM  its own Python environment, and this installs a different build of
REM  torch. Sharing an environment between them would swap the library
REM  out from under a run in progress - so this builds its OWN env in
REM  tools\voice-live\env and never touches the renderer's.
REM
REM  It will still fight the renderer for the machine. Wait until the
REM  barks are done, then run this.
REM ===================================================================

if /i "%~1"=="--fromtemp" goto :begin
copy /y "%~f0" "%TEMP%\ledger-canspeak.bat" >nul
"%TEMP%\ledger-canspeak.bat" --fromtemp
exit /b %errorlevel%
:begin

set "REPO=%USERPROFILE%\wc26-picks"
set "TOOL=%REPO%\tools\voice-live"
set "BRANCH=claude/game-dev-ai-automation-2h67ix"

if not exist "%REPO%\.git" goto :norepo

echo.
echo  LEDGER - can the cast speak live, on your GPU, at the quality of the barks?
echo  ==========================================================================
echo.
echo  If the bark render is still going, close this window and come back
echo  when it has finished.
echo.
pause

echo  Updating...
pushd "%REPO%"
git pull origin "%BRANCH%"
if errorlevel 1 goto :nopull
popd

where python >nul 2>nul || goto :nopython
cd /d "%TOOL%"

if not exist "env\Scripts\python.exe" (
  echo.
  echo  Building this probe's own environment. A few GB, once.
  echo.
  python -m venv env || goto :novenv
)
set "PY=%TOOL%\env\Scripts\python.exe"

"%PY%" -c "import torch_directml" >nul 2>nul
if errorlevel 1 (
  "%PY%" -m pip install --quiet --upgrade pip
  REM  DirectML, not CUDA and not CPU. This is the whole point: DirectX 12
  REM  compute runs on AMD, NVIDIA and Intel alike, which is the only kind
  REM  of answer a player could actually receive.
  echo  Installing torch + DirectML...
  "%PY%" -m pip install torch-directml
  echo  Installing onnxruntime-directml...
  "%PY%" -m pip install onnxruntime-directml
  echo  Installing chatterbox...
  "%PY%" -m pip install chatterbox-tts
  if errorlevel 1 goto :noinstall
)

echo.
echo  ---- what your machine can actually do ----------------------------
"%PY%" probe.py --backends
echo.
echo  ---- rendering one line, every route that works --------------------
"%PY%" probe.py --run
if errorlevel 1 goto :failed

if exist "%TOOL%\out\listen.html" start "" "%TOOL%\out\listen.html"

echo.
echo  ------------------------------------------------------------------
echo   A page should have opened with the clips side by side.
echo.
echo   The FIRST player is a real bark from the bank you just rendered.
echo   That is the bar. Every route below it has to sound like it belongs
echo   on the same street.
echo.
echo   TELL ME TWO THINGS:
echo     1. does any route sound as good as the bark
echo     2. the "x real time" figure printed above - under 1.0 means it
echo        can keep up with a conversation
echo  ------------------------------------------------------------------
echo.
pause
exit /b 0

:norepo
echo. & echo  No project at %REPO% & echo.
pause & exit /b 1

:nopull
popd
echo. & echo  The pull failed, so nothing ran. The reason is above. & echo.
pause & exit /b 1

:nopython
echo. & echo  Python is not installed. https://python.org/downloads & echo.
pause & exit /b 1

:novenv
echo. & echo  Could not create the environment. The reason is above. & echo.
pause & exit /b 1

:noinstall
REM  A FAILED INSTALL IS A RESULT, NOT A DEAD END. "torch-directml does not
REM  carry models of this shape" has sat in the plan for a week with no error
REM  message behind it. If it fails here, the message above IS the evidence
REM  that sentence never had.
echo.
echo  The install FAILED and nothing was rendered - the reason is above.
echo  Send me those lines. They are the answer either way: if DirectML
echo  cannot carry this model, that error is what tells us, and it is the
echo  first time anybody will have actually seen it.
echo.
pause & exit /b 1

:failed
echo.
echo  The probe FAILED - the reason is above. Send me those lines.
echo.
pause & exit /b 1
