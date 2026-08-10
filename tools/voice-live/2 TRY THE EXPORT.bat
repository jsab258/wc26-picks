@echo off
setlocal
title LEDGER - can chatterbox be converted?
REM ===================================================================
REM  THE QUESTION: can the engine that made your barks be converted into
REM  a form that runs on any gamer's graphics card?
REM
REM  We already know the hardware end works - your last run reported
REM  DirectML available on your AMD card. What is unknown is whether
REM  THIS model will convert, and it is built from three awkward pieces,
REM  so the honest answer is likely to be "two of the three".
REM
REM  This tries each piece separately and tells you which. That is the
REM  useful answer: if the big piece converts and the small one does
REM  not, the small one is the work left and the rest is done.
REM
REM  A FRESH ENVIRONMENT, AND THAT IS THE FIX FROM LAST TIME. The
REM  previous bat installed torch-directml and chatterbox together.
REM  They pin different torch versions - 2.4.1 against 2.6.0 - so pip
REM  swapped one for the other and left binaries that could not load.
REM  Nothing here installs torch-directml. It is not needed: converting
REM  happens once, on your machine, and the CONVERTED model runs through
REM  onnxruntime, which has no torch dependency at all.
REM ===================================================================

if /i "%~1"=="--fromtemp" goto :begin
copy /y "%~f0" "%TEMP%\ledger-export.bat" >nul
"%TEMP%\ledger-export.bat" --fromtemp
exit /b %errorlevel%
:begin

set "REPO=%USERPROFILE%\wc26-picks"
set "TOOL=%REPO%\tools\voice-live"
set "ENVDIR=%TOOL%\env-export"
set "BRANCH=claude/game-dev-ai-automation-2h67ix"

if not exist "%REPO%\.git" goto :norepo

echo.
echo  LEDGER - can chatterbox be converted?
echo  =====================================
echo.
echo  Updating...
pushd "%REPO%"
git pull origin "%BRANCH%"
if errorlevel 1 goto :nopull
popd

where python >nul 2>nul || goto :nopython
cd /d "%TOOL%"

REM ---- THE BROKEN ENVIRONMENT FROM LAST TIME -----------------------
REM  Told about, never deleted without asking. It is a few GB of your
REM  disk and it is unusable, but it is yours - CLAUDE.md rule 5 is a
REM  script that deleted 24 clips somebody had already picked from, and
REM  the lesson was to look before removing rather than to be helpful.
if exist "%TOOL%\env\Scripts\python.exe" (
  echo  NOTE: the previous probe's environment is still at
  echo        tools\voice-live\env
  echo        It is broken - that is the torch version clash - and it is
  echo        several GB. Nothing here touches it. Delete it whenever
  echo        you like; this run builds a separate clean one.
  echo.
)

REM  A VENV IS BROKEN WITHOUT pyvenv.cfg, AND python.exe BEING THERE PROVES
REM  NOTHING. This guard checked for the interpreter alone, so an environment
REM  missing its config file - which is exactly what happened today - was
REM  reported as present and then used, failing with "No pyvenv.cfg file" on
REM  every run and unable to repair itself. Check the file that makes it a
REM  venv, not the file that makes it look like one.
if not exist "%ENVDIR%\pyvenv.cfg" (
  if exist "%ENVDIR%" (
    echo   The environment is damaged - rebuilding it from scratch.
    rmdir /s /q "%ENVDIR%"
  )
)
if not exist "%ENVDIR%\Scripts\python.exe" (
  echo  Building a clean environment. A few GB, once.
  echo.
  python -m venv "%ENVDIR%" || goto :novenv
)
set "PY=%ENVDIR%\Scripts\python.exe"

"%PY%" -c "import chatterbox" >nul 2>nul
if errorlevel 1 (
  "%PY%" -m pip install --quiet --upgrade pip
  REM  CHATTERBOX FIRST AND ALONE, so its own pins win. Last time it was
  REM  installed second, on top of torch-directml's older torch, and the
  REM  resolver dragged in a transformers so new that chatterbox could no
  REM  longer import LlamaModel from it. Let one package own the stack.
  echo  Installing chatterbox and its own dependency set...
  "%PY%" -m pip install chatterbox-tts
  if errorlevel 1 goto :noinstall
  REM  onnxruntime-directml is added AFTER and pulls no torch, so it
  REM  cannot disturb what chatterbox just resolved.
  echo  Installing onnxruntime with DirectML...
  "%PY%" -m pip install onnxruntime-directml
  if errorlevel 1 goto :noinstall
)

REM ---- THE SECOND EXPORTER, AND IT MUST BE OUTSIDE THE BLOCK ABOVE -------
REM  Last run reported both big pieces as failing with
REM  "No module named 'onnxscript'". That is the newer exporter's own
REM  dependency, so the fallback never actually ran and two environment
REM  errors were reported as the model refusing to convert.
REM
REM  It is checked on its OWN rather than inside the first-time install,
REM  because your environment already exists - chatterbox imports, so that
REM  whole block is skipped and a package added inside it would never
REM  reach you. This is the same shape as the guard that only ever ran its
REM  failing case: the fix has to run on the machine that has the problem.
"%PY%" -c "import onnxscript" >nul 2>nul
if errorlevel 1 (
  echo  Installing onnxscript, which the newer exporter needs...
  "%PY%" -m pip install onnxscript
  if errorlevel 1 goto :noinstall
)

echo.
echo  ---- what this environment can do ---------------------------------
"%PY%" probe.py --backends

echo.
echo  ---- trying the conversion, one piece at a time --------------------
echo   Loading the model takes a minute or two. Each piece is tried on
echo   its own, so a failure on one does not hide the answer for the
echo   others.
echo.
"%PY%" export_probe.py --run
if errorlevel 2 goto :noimport
if errorlevel 1 goto :failed

if exist "%TOOL%\export-out" start "" "%TOOL%\export-out"

echo.
echo  ------------------------------------------------------------------
echo   Done. Send me what it printed, or the file
echo     tools\voice-live\export-out\export-report.json
echo.
echo   THREE OUTCOMES AND ALL THREE ARE USEFUL:
echo     all three pieces convert  - characters can talk, and the rest
echo                                 is wiring it into the game
echo     some convert              - the ones that failed are the work,
echo                                 and now we know which
echo     none convert              - we stop trying to keep this engine
echo                                 and bake the voices into a smaller
echo                                 one instead. Knowing that is worth
echo                                 the download.
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
echo.
echo  The install FAILED and nothing was converted - the reason is above.
echo  Send me those lines. An install error here is still a result: it
echo  says the environment is wrong, not that the model cannot convert.
echo.
pause & exit /b 1

:noimport
REM  A DISTINCT EXIT. "chatterbox will not import" and "the export failed"
REM  have completely different next steps, and the first bat reported
REM  them identically.
echo.
echo  chatterbox installed but will not import, so nothing was tried.
echo  That is an environment answer rather than a model answer - send me
echo  the line above and I will pin whatever is fighting.
echo.
pause & exit /b 2

:failed
echo.
echo  The probe itself failed - the reason is above. Send me those lines.
echo.
pause & exit /b 1
