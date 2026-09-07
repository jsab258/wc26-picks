@echo off
setlocal enabledelayedexpansion

REM  GIT MUST NEVER OPEN AN EDITOR HERE. 26 Aug: a `git pull` that made a
REM  merge commit opened vim in Jafar's window, he closed it, and the
REM  half-finished merge blocked every pull afterwards. `true` exits 0 at
REM  once so git takes the default message and carries on. The third one is
REM  the unattended guard: a credential prompt in a window nobody is
REM  watching waits for ever. tools\supervise.py sets all three on every git
REM  child it spawns as well, because a variable set here protects only the
REM  commands in here.
set "GIT_EDITOR=true"
set "GIT_MERGE_AUTOEDIT=no"
set "GIT_TERMINAL_PROMPT=0"

title LEDGER - everything
color 07

REM ===================================================================
REM  ONE WINDOW. THIS IS THE ONLY ONE YOU NEED.
REM
REM  Double-click this once. It starts the three things that have to
REM  stay running on this PC, keeps them running, and says at a glance
REM  which are up:
REM
REM    studio-watcher   the GPU and model work (props, pictures, voices)
REM    telegram-bot     the ONLY thing that sends to your phone, and the
REM                     only thing that reads what you type back
REM    claude-executor  turns an instruction you send from your phone into
REM                     a real working session, and puts the answer back
REM                     where the bot will send it to you
REM
REM  IT REPLACES TWO WINDOWS. You no longer need
REM  "START THE STUDIO MACHINE.bat" or "START THE TELEGRAM BOT.bat";
REM  both still work on their own, and running one of them AS WELL AS
REM  this would start a second copy of the same daemon. Use this one.
REM
REM  NOT REPLACED, because none of them stays running: "UPDATE FROM
REM  CLAUDE.bat" pulls and stops, "open-dashboard.bat" rebuilds the page
REM  and stops, "RUN THE STRANGER TEST.bat" runs one play session.
REM
REM  IF SOMETHING KEEPS CRASHING it is restarted with a growing wait,
REM  and after five stops in half an hour it is STOPPED and this window
REM  prints a box saying which one, why, and its own last words. Send
REM  that box. Nothing else stops when one thing does.
REM
REM  TO STOP EVERYTHING: close this window. Nothing is left running.
REM
REM  IT NEVER OPENS tools\runner\config.local. It checks that the file
REM  is there and says only that. No part of what is inside it is read,
REM  printed, or sent anywhere, by this file or by anything it starts.
REM
REM  NOTHING IS BOUGHT AND NO ACCOUNT IS USED.
REM
REM  THIS FILE HAS NEVER BEEN RUN WHERE IT WAS WRITTEN. There is no
REM  Windows in that container, so every DECISION it could get wrong
REM  lives in tools\supervise.py instead, which has a selftest that runs
REM  there; ledger\verify.py prints its count on every run. What is left up here is: find the
REM  project, find a python, hand over. The first double-click on this
REM  PC is this file's accepting test, per rule 5b.
REM ===================================================================

REM  RUN FROM A COPY. The supervisor brings the checkout up to date
REM  before it starts anything, and that can rewrite this very file
REM  while cmd.exe is still reading it by byte offset, which once made a
REM  script print the tail of its own replacement.
if /i "%~1"=="--fromtemp" goto :begin
copy /y "%~f0" "%TEMP%\ledger-everything.bat" >nul
if not exist "%TEMP%\ledger-everything.bat" (
  echo   Could not stage a working copy in %TEMP% - antivirus may have
  echo   blocked it. Tell Claude what this window says.
  pause & exit /b 1
)
"%TEMP%\ledger-everything.bat" --fromtemp
REM  Only reached when the working copy would not START. On success the
REM  line above transfers control and never comes back.
echo   The working copy would not start - antivirus may have blocked it.
echo   Tell Claude what this window says.
pause
exit /b 1
:begin

echo.
echo   LEDGER - everything
echo   ===================
echo.

REM --- where is the repository? ---------------------------------------
REM  The named path first, for the reason the studio machine gives: this
REM  file may be running from a TEMP copy, so one level up from it is
REM  nothing useful, and C:\Users\Jafar\wc26-picks is the path this
REM  machine actually uses.
set "REPO=%USERPROFILE%\wc26-picks"
if not exist "%REPO%\CLAUDE.md" set "REPO=%~dp0."
for %%I in ("%REPO%") do set "REPO=%%~fI"
if not exist "%REPO%\CLAUDE.md" (
  echo   COULD NOT FIND THE PROJECT.
  echo     looked in "%USERPROFILE%\wc26-picks"
  echo     and in    "%~dp0."
  echo   Move the project folder back to %USERPROFILE%\wc26-picks and
  echo   click this again. Nothing was started.
  goto :theend
)
cd /d "%REPO%"
echo   project : %REPO%

REM --- copy anything this machine made, somewhere git cannot reach -----
REM  Look before you destroy: a cancelled job once deleted 24 clips
REM  Jafar had already listened to, and reported success. The supervisor
REM  hard-resets this checkout once before it starts anything.
set "RESCUE=%USERPROFILE%\ledger-rescued"
mkdir "%RESCUE%" >nul 2>&1
copy /y "game-design\pc-jobs\result.txt" "%RESCUE%\" >nul 2>&1
copy /y "production\mesh-reports\*.txt" "%RESCUE%\" >nul 2>&1

REM --- find a python ---------------------------------------------------
REM  ANY Python 3.8+ runs the supervisor: it is standard library only.
REM  WHICH interpreter each daemon gets is decided in tools\supervise.py,
REM  where it is tested, because that decision is not the same for both:
REM  the watcher wants the voice environment when it exists (the voice
REM  jobs import torch) and the bot is stdlib only. Same search ORDER as
REM  every other launcher here.
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
  echo   NO PYTHON 3.8+ ON THIS PC, so nothing can be started.
  echo   Fix, one minute: install Python from the Microsoft Store or
  echo   from python.org and click this file again. Nothing is
  echo   installed into it.
  goto :theend
)
echo   python  : %PY%

if not exist "%REPO%\tools\runner\config.local" (
  echo   config  : MISSING at tools\runner\config.local. Everything else
  echo             starts; the Telegram bot cannot, and the window below
  echo             will say so by name every time it tries.
) else (
  echo   config  : present. Nothing here opens it.
)

echo.
%PY% "%REPO%\tools\supervise.py"
set "RC=%ERRORLEVEL%"

echo.
echo   THE SUPERVISOR ITSELF STOPPED, exit code %RC%. That is different
echo   from a daemon stopping: nothing is watching anything now. The
echo   lines above say why. Send them to Claude and click this file
echo   again.

:theend
echo.
echo   This window stays open so you can read it.
pause
endlocal
exit /b 0

REM --------------------------------------------------------------------
:trypy
if defined PY exit /b 0
if "%~1"=="" exit /b 0
if not exist "%~1" exit /b 0
"%~1" -c "import sys; sys.exit(0 if sys.version_info>=(3,8) else 1)" >nul 2>&1
if errorlevel 1 exit /b 0
REM  QUOTES GO IN THE VALUE: "C:\Program Files\..." unquoted would run
REM  "C:\Program" with an argument. `py -3` above must stay unquoted, so
REM  the quoting lives here rather than at the call site.
set PY="%~1"
exit /b 0
