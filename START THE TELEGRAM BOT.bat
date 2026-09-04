@echo off
setlocal
title LEDGER - the Telegram bot
REM ===================================================================
REM  ONE CLICK: starts the studio's Telegram bot on this PC and leaves
REM  it running. While this window is open the bot is alive; closing
REM  the window is how you stop it. Its silence is the signal that the
REM  studio is down, so if it goes quiet, that means something.
REM
REM  WHAT HAPPENS WHEN IT STARTS. It sends you two messages you did not
REM  ask for: one saying the channel is open, and one asking for the
REM  two budget readings with number buttons. Answer them, or type
REM  anything at all and it will answer you back.
REM
REM  IT NEVER PRINTS YOUR TOKEN. The bot reads tools\runner\config.local
REM  and nothing in this window, in any error message, or in anything
REM  Claude is ever sent contains any part of it.
REM
REM  NO GIT IN HERE, deliberately. This window must never stop and wait
REM  for a text editor nobody is watching, which is what a git command
REM  in a .bat did on this machine on 26 Aug. To get the latest code
REM  first, run "UPDATE FROM CLAUDE.bat" and then click this.
REM ===================================================================

set "REPO=%~dp0"
if "%REPO:~-1%"=="\" set "REPO=%REPO:~0,-1%"
if not exist "%REPO%\CLAUDE.md" set "REPO=%USERPROFILE%\wc26-picks"
if not exist "%REPO%\CLAUDE.md" (
  echo.
  echo   Could not find the LEDGER repository.
  echo   Looked next to this file and in "%USERPROFILE%\wc26-picks".
  goto :theend
)

echo.
echo   LEDGER - the Telegram bot
echo   =========================
echo.
echo   repo    : %REPO%

if not exist "%REPO%\tools\runner\config.local" (
  echo   config  : MISSING. Expected tools\runner\config.local here.
  echo             The bot will say the same thing and stop, and it
  echo             will name the two lines it wants.
) else (
  echo   config  : present. This window does not open it. The bot reads
  echo             it and never prints any part of what is in it.
)

REM --- find a python ---------------------------------------------------
REM  The bot is standard library only, so any Python 3.8+ runs it and
REM  nothing is installed. Same order as the other launchers here.
set "PY="
call :trypy "%USERPROFILE%\miniconda3\python.exe"
if not defined PY for /f "delims=" %%P in ('where python.exe 2^>nul') do call :trypy "%%P"
if not defined PY (
  py -3 -c "import sys" >nul 2>&1
  if not errorlevel 1 set "PY=py -3"
)
if not defined PY (
  echo.
  echo   NO PYTHON 3.8+ ON THIS PC, so the bot cannot start.
  echo   Fix, one minute: install Python from the Microsoft Store or
  echo   from python.org, then click this file again. Nothing is
  echo   installed into it.
  goto :theend
)
echo   python  : %PY%
echo.
echo   Starting. Leave this window open: closing it stops the bot.
echo   Every line below is timestamped and says what the bot is doing.
echo   A network wobble is retried by the bot itself and printed with a
echo   count; it does not stop.
echo.

%PY% "%REPO%\tools\runner\telegram-bot.py"
set "RC=%ERRORLEVEL%"

echo.
if "%RC%"=="0" (
  echo   The bot stopped cleanly. The last line above is its tally for
  echo   the whole run.
) else (
  echo   THE BOT STOPPED, exit code %RC%. The lines above say which of
  echo   these it was, in these words:
  echo     "config.local not found"        the file is not there
  echo     "no key matching"               the file is there and the
  echo                                     key names in it are ones the
  echo                                     bot does not know
  echo     "refused the token"             the token is wrong or revoked
  echo     "refused the chat id"           the chat id is wrong, or you
  echo                                     never pressed Start in the chat
  echo     "Could not reach Telegram"      this PC is offline
  echo   Send Claude those lines as they are. By construction they
  echo   contain nothing secret.
)

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
REM  "C:\Program" with an argument.
set PY="%~1"
exit /b 0
