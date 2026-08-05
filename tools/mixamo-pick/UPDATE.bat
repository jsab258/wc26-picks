@echo off
setlocal
title LEDGER - update
cd /d "%~dp0"

REM ===================================================================
REM  RUN FROM A COPY. A pull can rewrite this file while cmd.exe is
REM  reading it by byte offset, which is how a script ended up printing
REM  'nloads' - the tail of a URL from its own replacement.
REM ===================================================================
if /i "%~1"=="--fromtemp" goto :begin
copy /y "%~f0" "%TEMP%\ledger-%~n0.bat" >nul
"%TEMP%\ledger-%~n0.bat" --fromtemp
exit /b %errorlevel%
:begin

REM ===================================================================
REM  JUST PULLS. Nothing else.
REM
REM  This exists because "you need to pull to get the thing that pulls"
REM  came up three times in one afternoon. SETUP.bat pulls but then
REM  launches a two-hour harvest; FASTER.bat pulls but also re-tunes the
REM  harvester; PUSH.bat pulls but also pushes. None of them is the
REM  answer to "I just want the newest files".
REM ===================================================================

set "REPO=%USERPROFILE%\wc26-picks"
set "BRANCH=claude/game-dev-ai-automation-2h67ix"

echo.
echo  LEDGER - update
echo  ===============
echo.
if not exist "%REPO%\.git" goto :norepo
pushd "%REPO%"
git pull origin "%BRANCH%"
if errorlevel 1 goto :failed
popd
echo.
echo  ------------------------------------------------------------
REM  IT PULLS THE WHOLE REPOSITORY, and this line used to say only
REM  "everything in tools\mixamo-pick is current" - true when this
REM  folder was the only one with scripts in it, and quietly wrong
REM  once voice-gen existed. Somebody looking for the newest voice
REM  tools would have read that as "this did not update them".
echo   Up to date - the whole project, not just this folder.
echo.
echo   The scripts you can double-click live in:
echo     tools\voice-gen      the bark voices  (start with "1 RATE TEST")
echo     tools\voice-fetch    picking reference voices
echo     tools\mixamo-pick    bodies and animations
echo  ------------------------------------------------------------
pause & exit /b 0

:norepo
echo  No project at %REPO% - run SETUP.bat first.
pause & exit /b 1

:failed
popd
echo.
echo  The pull failed - the reason is above. Send it to me.
pause & exit /b 1
