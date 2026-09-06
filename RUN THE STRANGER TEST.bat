@echo off
setlocal enabledelayedexpansion
title Meridian
color 07

REM ===================================================================
REM  ONE EVENING, THREE PEOPLE, TWO RUNS EACH.
REM
REM  This is production/queue/119. Each person plays the same ten
REM  minutes twice. Something is different between their two runs and
REM  they are not told what, or that anything is. Afterwards you ask
REM  them the three questions on the sheet:
REM
REM      game-design\stranger-test-script.md
REM
REM  READ THAT SHEET BEFORE THE FIRST PERSON SITS DOWN. It is one page
REM  and it is the actual instrument; this file only starts the game.
REM
REM  HOW TO USE IT. Double-click. It asks who is playing (1, 2 or 3)
REM  and whether this is their first or second run, and starts. It
REM  never says on screen which version they are getting, so you can
REM  stay out of it too. The answer is written to
REM  production\stranger-test\runs.txt afterwards.
REM
REM  IT BUILDS FIRST, ON PURPOSE. Nobody should watch a compiler. The
REM  first build takes about half a minute and every one after it is
REM  instant, so run it once yourself before anybody arrives.
REM
REM  NOTHING IS BOUGHT, NOTHING IS INSTALLED, NOTHING GOES OVER THE
REM  NETWORK. The whole session runs on this machine with no API key
REM  and no internet: every word anybody says comes out of the game's
REM  own banks.
REM
REM  NEVER RUN WHERE IT WAS WRITTEN: there is no Windows in the
REM  container this came from, so the first run on the PC is this
REM  file's accepting test (rule 5b).
REM ===================================================================

set "REPO=%~dp0"
if "%REPO:~-1%"=="\" set "REPO=%REPO:~0,-1%"
if not exist "%REPO%\CLAUDE.md" set "REPO=%USERPROFILE%\wc26-picks"
if not exist "%REPO%\CLAUDE.md" (
  echo.
  echo   Could not find the LEDGER folder. Looked in "%~dp0" and in
  echo   "%USERPROFILE%\wc26-picks". Nothing was run.
  goto :theend
)

where dotnet >nul 2>&1
if errorlevel 1 (
  echo.
  echo   FAILED: the .NET SDK is not on this machine, so there is
  echo   nothing to run. Nothing was started.
  echo   Fix, about five minutes: install the .NET 8 SDK from
  echo   https://dotnet.microsoft.com/download  then double-click
  echo   this file again.
  goto :theend
)

echo.
echo   Getting ready. This is quick after the first time.
dotnet build -c Release -v q --nologo "%REPO%\ledger\StrangerTest\StrangerTest.csproj" >nul 2>&1
if errorlevel 1 (
  echo.
  echo   FAILED: the session would not build, so nothing was run and
  echo   nobody should be sat down in front of it yet. To see why:
  echo     dotnet build "%REPO%\ledger\StrangerTest\StrangerTest.csproj"
  goto :theend
)

echo.
set "WHO="
set /p WHO=  Who is playing (1, 2 or 3)?
if not "%WHO%"=="1" if not "%WHO%"=="2" if not "%WHO%"=="3" (
  echo.
  echo   That needs to be 1, 2 or 3. Nothing was run.
  goto :theend
)

set "RUN="
set /p RUN=  Is this their first or second run (1 or 2)?
if not "%RUN%"=="1" if not "%RUN%"=="2" (
  echo.
  echo   That needs to be 1 or 2. Nothing was run.
  goto :theend
)

REM  Hand the machine over. Nothing about which version this is has
REM  been printed, and nothing below prints it either.
cls
dotnet run -c Release --no-build --project "%REPO%\ledger\StrangerTest" -- --participant %WHO% --run %RUN%
set "RC=%errorlevel%"
if not "%RC%"=="0" (
  echo.
  echo   That run did not finish. What it managed is in
  echo   production\stranger-test\sessions, and the run is marked
  echo   ended=early in production\stranger-test\runs.txt. A run that
  echo   stopped is not an answer to anything: start it again.
)

:theend
echo.
pause
endlocal
