@echo off
setlocal
title LEDGER - export the graph the game drives
REM ===================================================================
REM  THE GRAPH WE HAVE TAKES THE WRONG THING.
REM
REM  The first export answered "can this model be converted at all".
REM  It can: the transformer agrees with the original to seven decimal
REM  places. That question is closed.
REM
REM  Writing the game's side of it found a different problem. The
REM  converted graph takes an EMBEDDING - the model's internal
REM  representation of a word-piece - and the game has a TOKEN, which
REM  is a number. Converting between them needs two lookup tables that
REM  live inside the model and are not in the exported file.
REM
REM  So the game would have to ship 50 MB of the model's own weights
REM  and redo a piece of the model itself. That is exactly the kind of
REM  thing that has gone wrong twice already here: both times the
REM  result was speech that sounded fine and was subtly wrong, with no
REM  error anywhere to catch it.
REM
REM  This exports a graph that takes the token directly. The lookup
REM  happens inside, where the weights already are, and the game hands
REM  over two numbers and nothing else.
REM
REM  ALREADY CHECKED WITHOUT YOUR HARDWARE, against a real model built
REM  small - same code, same wiring, 6 million weights instead of 520
REM  million, because converting does not care how big a number is. It
REM  agreed to seven decimal places, including at four positions in a
REM  sentence it was never shown. That last part is the one that
REM  matters: get it wrong and every word after the first is placed
REM  wrongly, and it still sounds like speech.
REM
REM  What this run adds is the real weights.
REM ===================================================================

if defined LEDGER_GAMEEXPORT_FROMTEMP goto :begin
set "LEDGER_GAMEEXPORT_FROMTEMP=1"
copy /y "%~f0" "%TEMP%\ledger-gameexport.bat" >nul
"%TEMP%\ledger-gameexport.bat" %*
exit /b %errorlevel%
:begin

set "REPO=%USERPROFILE%\wc26-picks"
set "TOOL=%REPO%\tools\voice-live"
set "ENVDIR=%TOOL%\env-export"
set "BRANCH=claude/game-dev-ai-automation-2h67ix"

if not exist "%REPO%\.git" goto :norepo

echo.
echo  LEDGER - export the graph the game drives
echo  =========================================
echo.
echo  Updating...
pushd "%REPO%"
git pull origin "%BRANCH%"
if errorlevel 1 goto :nopull
popd

if not exist "%ENVDIR%\Scripts\python.exe" goto :noenv
set "PY=%ENVDIR%\Scripts\python.exe"
cd /d "%TOOL%"

echo.
echo  ---- exporting -----------------------------------------------------
echo   The model loads first, a minute or two. Then one line runs to shape
echo   the graph against a real memory cache, and the graph is written and
echo   immediately checked against the original - including at positions it
echo   was not traced at, which is the failure worth catching.
echo.
"%PY%" export-for-game.py %*
if errorlevel 2 goto :noimport
if errorlevel 1 goto :failed

if exist "%TOOL%\game-out" start "" "%TOOL%\game-out"

echo.
echo  ------------------------------------------------------------------
echo   Send me what it printed. The two numbers that matter are the
echo   agreement at the traced position and the agreement at the four it
echo   was NOT traced at - if the second is much worse than the first,
echo   the position got baked in and I need to know before anything is
echo   built on top of it.
echo.
echo   The .onnx file itself stays on your disk for now - it is about
echo   2 GB and does not belong in git. Shipping it with the game is
echo   settled; how it gets there is a later problem.
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

:noenv
echo.
echo  The export environment is not there yet. Run "2 TRY THE EXPORT.bat"
echo  first - it builds it and downloads the model.
echo.
pause & exit /b 1

:noimport
echo.
echo  The model would not load, so nothing was exported. That is an
echo  environment answer rather than a model one - send me the line above.
echo.
pause & exit /b 2

:failed
echo.
echo  It ran but did not finish - the reason is above. Send me those
echo  lines. A refusal here is still a result: it says which part of the
echo  wrapper the exporter will not take, and that is a short list.
echo.
pause & exit /b 1
