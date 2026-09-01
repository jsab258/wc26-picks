@echo off
setlocal enabledelayedexpansion
title LEDGER - status dashboard
color 07

REM ===================================================================
REM  ONE CLICK. Double-click this and the status page opens in your
REM  browser, rebuilt from the project files first so it is not a
REM  picture of yesterday.
REM
REM  WHAT IT DOES
REM    1. Rebuilds dashboard.html and STATUS.md from the repository.
REM    2. Opens dashboard.html in whatever browser you normally use.
REM    The page refreshes itself every 5 minutes, and it says how old
REM    it is at the top, so a regenerator that has stopped shows up as
REM    a number rather than as a page that looks current.
REM
REM  THREE MODES
REM    (double-click)  rebuild, then open the page.
REM    /refresh        rebuild only. This is what the scheduled task runs.
REM    /register       create the Windows task that rebuilds every 15
REM                    minutes. Run once. /unregister removes it.
REM
REM  IT RUNS NO GIT ON PURPOSE. A pull every fifteen minutes on this
REM  machine would make merge commits behind the build agent's back,
REM  which is a way to lose work rather than a way to stay current. The
REM  page describes THIS CHECKOUT and names the folder it read at the
REM  bottom; use "UPDATE FROM CLAUDE.bat" when you want newer files.
REM  (No git means tools/lint-bat-editor.py has nothing to ask of this
REM  file. If a git command is ever added here, GIT_EDITOR must be set
REM  in the same edit.)
REM
REM  NOTHING IS BOUGHT, NO ACCOUNT IS USED, NOTHING IS INSTALLED.
REM
REM  NEVER RUN WHERE IT WAS WRITTEN: there is no Windows in the
REM  container this came from, so the first run here is this file's
REM  accepting test (rule 5b). Every DECISION lives in the Python,
REM  which is tested: this file only finds a Python and opens a page.
REM ===================================================================

set "MODE=%~1"

REM --- where is the repository? ---------------------------------------
set "REPO=%~dp0"
if "%REPO:~-1%"=="\" set "REPO=%REPO:~0,-1%"
if not exist "%REPO%\CLAUDE.md" set "REPO=%USERPROFILE%\wc26-picks"
if not exist "%REPO%\CLAUDE.md" (
  echo   NOTE: could not find the LEDGER repository.
  echo         Looked in "%~dp0" and "%USERPROFILE%\wc26-picks".
  echo         Without it there is nothing to read and no page to make.
  goto :theend
)

if /I "%MODE%"=="/register" goto :register
if /I "%MODE%"=="/unregister" goto :unregister

REM --- a Python to run the generator ----------------------------------
REM  Stdlib only, so any Python 3.8+ works and nothing is installed.
set "PY="
call :trypy "%REPO%\tools\voice-live\env-export\Scripts\python.exe"
call :trypy "%USERPROFILE%\miniconda3\python.exe"
if not defined PY for /f "delims=" %%P in ('where python.exe 2^>nul') do call :trypy "%%P"
if not defined PY (
  py -3 -c "import sys" >nul 2>&1
  if not errorlevel 1 set "PY=py -3"
)
if not defined PY (
  echo.
  echo   FAILED: no Python 3.8+ on this machine, so the page cannot be
  echo   rebuilt. Any older dashboard.html on disk is left alone and is
  echo   as old as its own timestamp says.
  echo   Fix, one minute: install Python from the Microsoft Store or
  echo   python.org, then double-click this file again.
  goto :theend
)

echo.
echo   LEDGER - rebuilding the status page from %REPO%
%PY% "%REPO%\tools\dashboard\build-dashboard.py" --repo "%REPO%"
set "RC=%errorlevel%"
if not "%RC%"=="0" (
  echo.
  if "%RC%"=="3" echo   STOPPED: that folder does not look like the LEDGER repo. Nothing was written.
  if "%RC%"=="4" echo   STOPPED: a helper this tool refuses to run without is missing. Nothing was written.
  if "%RC%"=="2" echo   STOPPED: the write failed. The reason is above.
  if "%RC%"=="1" echo   STOPPED: the generator's selftest failed. The reason is above.
  echo   The page was NOT rebuilt. Anything on screen from an older run
  echo   is that old; do not read it as current.
  goto :theend
)

if /I "%MODE%"=="/refresh" (
  echo   Rebuilt. Not opening a browser (/refresh).
  goto :theend
)

echo   Opening dashboard.html ...
start "" "%REPO%\dashboard.html"
goto :theend

:register
REM  Every 15 minutes, forever, rebuild only. /F replaces an existing
REM  entry so running this twice is safe rather than an error.
schtasks /Create /TN "LEDGER-dashboard" /TR "\"%REPO%\open-dashboard.bat\" /refresh" /SC MINUTE /MO 15 /F
if errorlevel 1 (
  echo   COULD NOT REGISTER the task. The line above says why. The page
  echo   can still be rebuilt by double-clicking this file.
) else (
  echo   Registered LEDGER-dashboard: rebuilds every 15 minutes.
  echo   Remove it with:  open-dashboard.bat /unregister
)
goto :theend

:unregister
schtasks /Delete /TN "LEDGER-dashboard" /F
if errorlevel 1 (
  echo   Nothing to remove, or it could not be removed. The line above says which.
) else (
  echo   Removed LEDGER-dashboard. The page no longer rebuilds on its own,
  echo   so from now on it is only as fresh as the last double-click.
)
goto :theend

REM --------------------------------------------------------------------
:trypy
if defined PY exit /b 0
if "%~1"=="" exit /b 0
if not exist "%~1" exit /b 0
"%~1" -c "import sys; sys.exit(0 if sys.version_info>=(3,8) else 1)" >nul 2>&1
if errorlevel 1 exit /b 0
REM  QUOTES GO IN THE VALUE: "C:\Program Files\..." unquoted would run
REM  "C:\Program" with an argument.
set PY="%~1"
exit /b 0

:theend
echo.
if /I not "%MODE%"=="/refresh" pause
endlocal
