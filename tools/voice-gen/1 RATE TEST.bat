@echo off
setlocal
title LEDGER - voice rate test
REM ===================================================================
REM  LEDGER 17.2, step 1 of 2. DOUBLE-CLICK THIS. Nothing to do first.
REM
REM  It pulls the newest code, installs what it needs into its own
REM  folder, renders twenty bark lines on your GPU, prints how long each
REM  took, and opens the folder so you can listen to them.
REM
REM  Nothing here touches the rest of your machine: the packages go in
REM  tools\voice-gen\env, and deleting that folder undoes all of it.
REM ===================================================================

REM ---- RUN FROM A COPY, BECAUSE THIS FILE IS ABOUT TO PULL ----------
REM  A pull can rewrite this script while cmd.exe is still reading it by
REM  byte offset. That is not hypothetical here: it produced 'nloads' is
REM  not recognized - the tail of a URL - from a script replaced
REM  underneath itself mid-run. Same guard as UPDATE.bat and PUSH.bat.
if /i "%~1"=="--fromtemp" goto :begin
copy /y "%~f0" "%TEMP%\ledger-ratetest.bat" >nul
"%TEMP%\ledger-ratetest.bat" --fromtemp
exit /b %errorlevel%
:begin

REM  ABSOLUTE PATHS FROM HERE ON. The copy runs from TEMP, so %~dp0 is
REM  no longer the tool folder and every relative path would miss.
set "REPO=%USERPROFILE%\wc26-picks"
set "TOOL=%REPO%\tools\voice-gen"
set "BRANCH=claude/game-dev-ai-automation-2h67ix"

if not exist "%REPO%\.git" goto :norepo

echo.
echo  LEDGER - voice rate test
echo  ========================
echo.
echo  Updating...
pushd "%REPO%"
git pull origin "%BRANCH%"
if errorlevel 1 goto :nopull
popd

where python >nul 2>nul || goto :nopython
cd /d "%TOOL%"

REM ---- the environment, built once ---------------------------------
REM  Its own venv rather than your global python, because chatterbox
REM  pulls a specific torch and this must not be able to break anything
REM  else you have installed.
if not exist "env\Scripts\python.exe" (
  echo.
  echo  First run - building the environment. This downloads a few GB
  echo  and takes a while. It only ever happens once.
  echo.
  python -m venv env || goto :novenv
)
set "PY=%TOOL%\env\Scripts\python.exe"

"%PY%" -c "import chatterbox" >nul 2>nul
if errorlevel 1 (
  echo  Installing torch with CUDA support...
  "%PY%" -m pip install --quiet --upgrade pip
  REM  CUDA 12.1 wheels. If your card wants a different build this is the
  REM  one line to change, and the script says so rather than failing at
  REM  a rate of nought.
  "%PY%" -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
  echo  Installing chatterbox...
  "%PY%" -m pip install chatterbox-tts
  if errorlevel 1 goto :noinstall
)

echo.
echo  ==================================================================
echo   Rendering twenty lines. The FIRST one includes loading the model
echo   and will be much slower than the rest - that is expected and the
echo   script prints the whole series so you can see it.
echo  ==================================================================
echo.

"%PY%" ledger_voice_gen.py --rate 20
if errorlevel 2 goto :nomodel
if errorlevel 1 goto :failed

REM ---- let him HEAR it ---------------------------------------------
REM  The rate is half the point. The other half is whether a line at
REM  0.30 and a line at 0.80 actually sound differently directed - the
REM  sample is one line per direction band for exactly that reason, and
REM  a number cannot answer it.
set "OUT=%REPO%\ledger\Assets\Resources\voice\barks"
if exist "%OUT%" start "" "%OUT%"

echo.
echo  ------------------------------------------------------------------
echo   Done. The folder that opened has the twenty clips in it.
echo.
echo   TWO THINGS TO TELL ME:
echo     1. the median seconds-per-line printed above
echo     2. whether the quiet ones and the loud ones actually sound
echo        differently directed, or whether they all sound the same
echo.
echo   If they all sound the same, my direction map is wrong and it is
echo   much better to know that now than after three hundred renders.
echo  ------------------------------------------------------------------
echo.
pause
exit /b 0

:norepo
echo.
echo  No project at %REPO%
echo  That is where every other LEDGER script expects it too, so if you
echo  have it somewhere else, tell me and I will fix the path.
echo.
pause & exit /b 1

:nopull
popd
echo.
echo  The PULL failed, so nothing was rendered - you would have been
echo  testing yesterday's code. The reason is above. Send me those lines.
echo.
pause & exit /b 1

:nopython
echo.
echo  Python is not installed. Get it from https://python.org/downloads
echo  On the installer's FIRST screen, tick "Add python.exe to PATH".
echo.
pause & exit /b 1

:novenv
echo.
echo  Could not create the environment. The reason is above.
echo.
pause & exit /b 1

:noinstall
echo.
echo  The install FAILED - the reason is above, and nothing was rendered.
echo  Most likely it is the torch line: if your card is not CUDA 12.x,
echo  the --index-url in this .bat is the one thing to change.
echo  Send me those lines.
echo.
pause & exit /b 1

:nomodel
REM  A DISTINCT EXIT, because "chatterbox is missing" and "the render
REM  went wrong" have completely different next steps and the first
REM  version of this file would have reported them identically.
echo.
echo  chatterbox did not load, so NOTHING was rendered and there is no
echo  rate. The reason is above. Send me those lines.
echo.
pause & exit /b 2

:failed
REM  NO UNCONDITIONAL SUCCESS BANNER. "1 LISTEN.bat" carries the note
REM  about why: its first real run failed to reach any corpus and
REM  cheerfully announced that a page had opened.
echo.
echo  The render FAILED and there is no rate - the reason is above.
echo  Nothing is broken on your machine; send me those lines.
echo.
pause & exit /b 1
