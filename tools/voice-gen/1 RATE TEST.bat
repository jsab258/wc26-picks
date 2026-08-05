@echo off
setlocal
title LEDGER - voice rate test
REM ===================================================================
REM  LEDGER 17.2, step 1 of 2. DOUBLE-CLICK THIS.
REM
REM  It installs what it needs into its own folder, renders twenty bark
REM  lines on your GPU, prints how long each took, and opens the folder
REM  so you can listen to them.
REM
REM  Nothing here touches the rest of your machine: the packages go in
REM  tools\voice-gen\env, and deleting that folder undoes all of it.
REM ===================================================================
cd /d "%~dp0"

where python >nul 2>nul || (
  echo.
  echo  Python is not installed. Get it from https://python.org/downloads
  echo  On the installer's FIRST screen, tick "Add python.exe to PATH".
  echo.
  pause
  exit /b 1
)

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
set "PY=%~dp0env\Scripts\python.exe"

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
set "OUT=%~dp0..\..\ledger\Assets\Resources\voice\barks"
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
REM  THIS USED TO BE AN UNCONDITIONAL BANNER in the sibling script, and
REM  "1 LISTEN.bat" carries the note about it: the first real run failed
REM  to reach any corpus and cheerfully announced a page had opened.
echo.
echo  The render FAILED and there is no rate - the reason is above.
echo  Nothing is broken on your machine; send me those lines.
echo.
pause & exit /b 1
