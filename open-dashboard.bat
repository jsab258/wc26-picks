@echo off
setlocal enabledelayedexpansion
title LEDGER - status dashboard
color 07

REM ===================================================================
REM  NO CLICK NEEDED. Once /register has been run, this rebuilds itself
REM  every 15 minutes and each rebuild first brings the checkout up to
REM  date, so the page you open is built from CURRENT files. Double-
REM  click only when you want it opened now.
REM
REM  WHAT IT DOES
REM    1. Brings this checkout current: git pull --ff-only. Never a
REM       bare pull, so it can never make a merge commit.
REM    2. Rebuilds dashboard.html and STATUS.md from the repository.
REM    3. Opens dashboard.html in whatever browser you normally use.
REM    The page refreshes itself every 5 minutes, says how old IT is at
REM    the top, and now says how old the FILES it read are, because a
REM    page regenerated thirty seconds ago from a six-hour-old pull
REM    reads as current and is not.
REM
REM  THREE MODES
REM    (double-click)  update, rebuild, then open the page.
REM    /refresh        update and rebuild only. The scheduled task.
REM    /register       create the Windows task that does that every 15
REM                    minutes. Run once. /unregister removes it.
REM
REM  WHY A PULL IS ALLOWED HERE NOW, 2 Sep. This file used to run no git
REM  at all, because on 26 Aug a `git pull` made a merge commit, opened
REM  vim in Jafar's window, and the half-finished merge blocked every
REM  pull afterwards. `git pull --ff-only` is not that command: it moves
REM  the branch pointer or it REFUSES, it can never merge and never
REM  opens an editor, and on a refusal it changes nothing at all. The
REM  rule kept from that incident is NEVER MERGE UNATTENDED. A refused
REM  fast-forward, a failed fetch and a machine with no network are all
REM  REPORTED on the page and never resolved here.
REM
REM  EVERY DECISION IS IN THE PYTHON, which is tested. Whether to pull,
REM  whether a build is running, how far behind this clone is and every
REM  word of what the page says about it live in
REM  tools/dashboard/build-dashboard.py. This file finds a Python, hands
REM  it one word, and opens a page.
REM
REM  NOTHING IS BOUGHT, NO ACCOUNT IS USED, NOTHING IS INSTALLED.
REM
REM  NEVER RUN WHERE IT WAS WRITTEN: there is no Windows in the
REM  container this came from, so the first run here is this file's
REM  accepting test (rule 5b).
REM ===================================================================

REM  GIT MUST NEVER OPEN AN EDITOR AND MUST NEVER WAIT FOR A PASSWORD.
REM  The first two are the 26 Aug guards that tools/lint-bat-editor.py
REM  asks of any .bat that reaches git. The third is the unattended one:
REM  a credential prompt inside a scheduled task with no window waits
REM  for ever, and a refresh that hangs is a page that quietly stops
REM  being rebuilt. The Python sets all three on the git child as well.
set "GIT_EDITOR=true"
set "GIT_MERGE_AUTOEDIT=no"
set "GIT_TERMINAL_PROMPT=0"

REM --- run from a copy of this file, then it can safely be replaced ---
REM  A pull can rewrite THIS FILE while cmd.exe is still reading it by
REM  byte offset, which has produced half-a-URL error messages from
REM  other scripts on this machine, and a garbage resume could land in
REM  the /unregister block below and silently delete the scheduled task.
REM  So: hand off to a copy in %TEMP% and let the pull rewrite the
REM  original underneath us. Same trick, same reason, as
REM  "UPDATE FROM CLAUDE.bat".
set "MODE=%~1"
set "CHECKOUT=refresh"
if /I "%~1"=="--fromtemp" (
  set "MODE=%~2"
  set "REPO=%~3"
  set "CHECKOUT=%~4"
  goto :fromcopy
)
set "REPO=%~dp0"
if "%REPO:~-1%"=="\" set "REPO=%REPO:~0,-1%"
copy /y "%~f0" "%TEMP%\ledger-dashboard-run.bat" >nul 2>&1
if exist "%TEMP%\ledger-dashboard-run.bat" (
  "%TEMP%\ledger-dashboard-run.bat" --fromtemp "%MODE%" "%REPO%" "%CHECKOUT%"
  exit /b !errorlevel!
)
REM  No working copy, so NO PULL: rebuilding in place is safe, pulling
REM  in place is the byte-offset hazard above. The page says which of
REM  the two happened; `skip-no-working-copy` is the Python's word for
REM  it and the sentence the reader sees is written there.
echo   NOTE: could not make a working copy in %TEMP% - antivirus may
echo         have blocked it. Rebuilding WITHOUT updating first; the
echo         page will say so where it says how old the files are.
set "CHECKOUT=skip-no-working-copy"
:fromcopy

REM --- where is the repository? ---------------------------------------
if not exist "%REPO%\CLAUDE.md" set "REPO=%USERPROFILE%\wc26-picks"
if not exist "%REPO%\CLAUDE.md" (
  echo   NOTE: could not find the LEDGER repository.
  echo         Looked in "%REPO%" and "%USERPROFILE%\wc26-picks".
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
  echo   FAILED: no Python 3.8+ on this machine, so nothing was updated
  echo   and the page cannot be rebuilt. Any older dashboard.html on
  echo   disk is left alone and is as old as its own timestamp says.
  echo   Fix, one minute: install Python from the Microsoft Store or
  echo   python.org, then double-click this file again.
  goto :theend
)

echo.
echo   LEDGER - updating and rebuilding the status page from %REPO%
%PY% "%REPO%\tools\dashboard\build-dashboard.py" --repo "%REPO%" --checkout %CHECKOUT%
set "RC=%errorlevel%"
if not "%RC%"=="0" (
  echo.
  if "%RC%"=="3" echo   STOPPED: that folder does not look like the LEDGER repo. Nothing was written.
  if "%RC%"=="4" echo   STOPPED: a helper this tool refuses to run without is missing. Nothing was written.
  if "%RC%"=="2" echo   STOPPED: the write failed, or this launcher asked for an option the generator does not accept. The reason is above.
  if "%RC%"=="1" echo   STOPPED: the generator's selftest failed. The reason is above.
  echo   The page was NOT rebuilt. Anything on screen from an older run
  echo   is that old; do not read it as current.
  goto :theend
)

if /I "%MODE%"=="/refresh" (
  echo   Updated and rebuilt. Not opening a browser (/refresh).
  goto :theend
)

echo   Opening dashboard.html ...
start "" "%REPO%\dashboard.html"
goto :theend

:register
REM  Every 15 minutes, forever: update then rebuild, no browser. /F
REM  replaces an existing entry so running this twice is safe rather
REM  than an error. It registers the ORIGINAL path, never the copy.
schtasks /Create /TN "LEDGER-dashboard" /TR "\"%REPO%\open-dashboard.bat\" /refresh" /SC MINUTE /MO 15 /F
if errorlevel 1 (
  echo   COULD NOT REGISTER the task. The line above says why. The page
  echo   can still be rebuilt by double-clicking this file.
) else (
  echo   Registered LEDGER-dashboard: pulls and rebuilds every 15 minutes.
  echo   Remove it with:  open-dashboard.bat /unregister
)
goto :theend

:unregister
schtasks /Delete /TN "LEDGER-dashboard" /F
if errorlevel 1 (
  echo   Nothing to remove, or it could not be removed. The line above says which.
) else (
  echo   Removed LEDGER-dashboard. Nothing updates or rebuilds on its own
  echo   now, so from now on the page is only as fresh as the last
  echo   double-click, and it will say so.
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
