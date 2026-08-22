@echo off
setlocal
title LEDGER - get the latest from Claude
REM ===================================================================
REM  ONE CLICK: pulls everything Claude has pushed since you last
REM  looked - tools, scripts, docs - and says what arrived.
REM
REM  RUN FROM A COPY, and for this script it is not a nicety: a pull
REM  can rewrite THIS FILE while cmd.exe is still reading it by byte
REM  offset, which has produced half-a-URL error messages from other
REM  scripts on this machine.
REM ===================================================================
if /i "%~1"=="--fromtemp" goto :begin
copy /y "%~f0" "%TEMP%\ledger-update.bat" >nul
"%TEMP%\ledger-update.bat" --fromtemp
exit /b %errorlevel%
:begin

set "REPO=%USERPROFILE%\wc26-picks"
set "BRANCH=claude/game-dev-ai-automation-2h67ix"

if not exist "%REPO%\.git" (
  echo  No project at %REPO%
  pause & exit /b 1
)
cd /d "%REPO%"

echo.
echo  LEDGER - get the latest from Claude
echo  ===================================
echo.
git fetch origin "%BRANCH%"
if errorlevel 1 goto :fail

for /f %%c in ('git rev-list --count HEAD..origin/%BRANCH%') do set BEHIND=%%c
if "%BEHIND%"=="0" (
  echo  Already up to date - nothing new since your last pull.
  echo.
  pause & exit /b 0
)

echo  %BEHIND% new change(s). What arrived:
echo  ------------------------------------
git --no-pager log --oneline HEAD..origin/%BRANCH% -15
echo  ------------------------------------
echo.
git pull origin "%BRANCH%"
if errorlevel 1 goto :fail

echo.
echo  DONE - everything is current.
echo.
pause
exit /b 0

:fail
echo.
echo  The pull FAILED - the reason is above. The commonest cause is
echo  local edits in the way: tell Claude what it printed.
echo.
pause & exit /b 1
