@echo off
setlocal
title LEDGER - check the exported graphs
REM ===================================================================
REM  THIS ONE SENDS ITS OWN ANSWER BACK. NOTHING TO COPY.
REM
REM  The last run worked and its answer never reached me, because the
REM  only way out of it was you selecting text in a console window.
REM  That is my fault, not yours - a report that depends on somebody
REM  remembering to copy it is a report that eventually goes missing,
REM  and this one did.
REM
REM  So this writes what it finds into a file inside the project and
REM  pushes it, the same way the game's screenshots come back to me.
REM
REM  It is also FAST - seconds, not minutes. It reads the two exported
REM  files directly and never loads the 2 GB model, because the two
REM  faults worth catching do not need it. Both are the same shape:
REM  something that should be a dial the game can turn got frozen into
REM  the file as a fixed value. Once frozen it cannot disagree with
REM  itself, so running the graph twice with two different settings and
REM  watching whether the answer moves is the whole test.
REM
REM  Frozen voice: every character in the game speaks as one person.
REM  Frozen position: every word after the first sits in the wrong
REM  place in the sentence.
REM
REM  Both sound completely fluent. Neither raises an error.
REM ===================================================================

if defined LEDGER_CHECKGRAPHS_FROMTEMP goto :begin
set "LEDGER_CHECKGRAPHS_FROMTEMP=1"
copy /y "%~f0" "%TEMP%\ledger-checkgraphs.bat" >nul
"%TEMP%\ledger-checkgraphs.bat" %*
exit /b %errorlevel%
:begin

set "REPO=%USERPROFILE%\wc26-picks"
set "TOOL=%REPO%\tools\voice-live"
set "ENVDIR=%TOOL%\env-export"
set "BRANCH=claude/game-dev-ai-automation-2h67ix"
set "REPORT=%REPO%\game-design\voice-live\export-report.txt"

if not exist "%REPO%\.git" goto :norepo

echo.
echo  LEDGER - check the exported graphs
echo  ==================================
echo.
echo  Updating...
pushd "%REPO%"
git pull origin "%BRANCH%"
if errorlevel 1 goto :nopull

if not exist "%ENVDIR%\Scripts\python.exe" goto :noenv
set "PY=%ENVDIR%\Scripts\python.exe"

echo.
echo  ---- checking ------------------------------------------------------
"%PY%" "%TOOL%\check-graphs.py"
set "AUDIT=%errorlevel%"
if "%AUDIT%"=="2" goto :noimport

echo.
echo  ---- sending it back -----------------------------------------------
if not exist "%REPORT%" goto :noreport
git add "%REPORT%"
git commit -m "Graph audit from Jafar's machine" >nul 2>&1
git pull --rebase origin "%BRANCH%" >nul 2>&1
git push origin HEAD:"%BRANCH%"
if errorlevel 1 goto :nopush
popd
echo.
echo   Sent. Nothing for you to copy - I will read it from the project.
echo.
pause
exit /b %AUDIT%

:noreport
popd
echo.
echo   The check did not write a report, so there is nothing to send.
echo   That is a fault in my tool rather than in the graphs - send me
echo   whatever it printed above.
echo.
pause & exit /b 1

:nopush
popd
echo.
echo   The check ran and the report was written, but pushing it failed -
echo   the reason is above. Opening it now: send me this file, or just
echo   paste its contents.
echo.
start "" notepad "%REPORT%"
pause & exit /b 1

:norepo
echo. & echo  No project at %REPO% & echo.
pause & exit /b 1

:nopull
popd
echo. & echo  The pull failed, so nothing ran. The reason is above. & echo.
pause & exit /b 1

:noenv
popd
echo.
echo  The export environment is not there yet. Run "2 TRY THE EXPORT.bat"
echo  first - it builds it and downloads the model.
echo.
pause & exit /b 1

:noimport
popd
echo.
echo  onnxruntime would not load, so nothing was checked. That is an
echo  environment answer rather than a graph one - send me the line above.
echo.
pause & exit /b 2
