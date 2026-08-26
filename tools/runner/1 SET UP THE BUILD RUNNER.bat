@echo off
setlocal
REM  GIT MUST NEVER OPEN AN EDITOR HERE. 26 Aug: a `git pull` that made a
REM  merge commit opened vim in Jafar's window, he closed it, and the
REM  half-finished merge blocked every pull afterwards - which then read
REM  as "the pull is broken" rather than "something is waiting for you".
REM  `true` is a program that exits 0 immediately, so git takes the default
REM  message and carries on. TWENTY-TWO .bat files ran `git pull` and NOT
REM  ONE guarded this: one idea, twenty-two implementations, in scripts
REM  whose entire purpose is that nobody is watching the window.
set "GIT_EDITOR=true"
set "GIT_MERGE_AUTOEDIT=no"

title LEDGER - move the builds onto this PC
REM ===================================================================
REM  RUN FROM A COPY. This script may pull, and a pull can rewrite THIS
REM  FILE while cmd.exe is still reading it by byte offset.
REM ===================================================================
if /i "%~1"=="--fromtemp" goto :begin
copy /y "%~f0" "%TEMP%\ledger-runner.bat" >nul
"%TEMP%\ledger-runner.bat" --fromtemp
exit /b %errorlevel%
:begin

REM ===================================================================
REM  WHAT THIS DOES, in one breath: installs GitHub's small build agent
REM  on this PC as a background service, so LEDGER's Windows builds run
REM  HERE instead of on a rented blank machine. Your GPU renders the
REM  simulation about twenty times faster and the Unity install caches
REM  between builds, so the ~28 minute round trip drops to roughly
REM  6-10 minutes after the first run.
REM
REM  YOU NEED: about 20 GB free on C:, and one paste - GitHub shows a
REM  registration token on a page only you can open, and this script
REM  stops and asks for it at the right moment.
REM
REM  RUN AS ADMINISTRATOR (right-click this file, "Run as
REM  administrator") - installing a Windows service needs it.
REM ===================================================================

net session >nul 2>&1
if errorlevel 1 (
  echo.
  echo  This needs administrator rights to install the service.
  echo  Close this window, RIGHT-CLICK the file and pick
  echo  "Run as administrator".
  echo.
  pause & exit /b 1
)

set "REPO=%USERPROFILE%\wc26-picks"
set "RUNNERDIR=C:\actions-runner-ledger"
set "RUNNERVER=2.321.0"
set "RUNNERZIP=actions-runner-win-x64-%RUNNERVER%.zip"
set "RUNNERURL=https://github.com/actions/runner/releases/download/v%RUNNERVER%/%RUNNERZIP%"
set "BRANCH=claude/game-dev-ai-automation-2h67ix"

echo.
echo  LEDGER - move the builds onto this PC
echo  =====================================
echo.

if exist "%RUNNERDIR%\.runner" (
  echo  A runner is already configured in %RUNNERDIR%.
  echo  Nothing to do. If builds are not arriving, check that the
  echo  "GitHub Actions Runner" service is running in services.msc.
  echo.
  pause & exit /b 0
)

echo  ---- downloading the build agent (about 100 MB) --------------------
if not exist "%RUNNERDIR%" mkdir "%RUNNERDIR%"
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol='Tls12'; Invoke-WebRequest -Uri '%RUNNERURL%' -OutFile '%RUNNERDIR%\%RUNNERZIP%'"
if errorlevel 1 goto :downloadfail

echo  ---- unpacking ------------------------------------------------------
powershell -NoProfile -Command "Expand-Archive -Force '%RUNNERDIR%\%RUNNERZIP%' '%RUNNERDIR%'"
if errorlevel 1 goto :unpackfail

echo.
echo  ------------------------------------------------------------------
echo   ONE PASTE FROM YOU. Open this page in your browser (it needs
echo   your GitHub login, which is why this script cannot do it):
echo.
echo     https://github.com/jsab258/wc26-picks/settings/actions/runners/new
echo.
echo   Pick "Windows x64" if it asks. On that page, find the line that
echo   looks like:
echo.
echo     ./config.cmd --url ... --token XXXXXXXXXXXXXXXXXXXXX
echo.
echo   Copy ONLY the token (the XXXX part) and paste it below.
echo   The token expires after about an hour, so paste it now.
echo  ------------------------------------------------------------------
echo.
set /p TOKEN="  paste the token here and press Enter: "
if "%TOKEN%"=="" ( echo  Nothing pasted - stopping. & pause & exit /b 1 )

echo.
echo  ---- registering this PC as the build machine ----------------------
cd /d "%RUNNERDIR%"
call config.cmd --url https://github.com/jsab258/wc26-picks --token %TOKEN% --name ledger-pc --labels ledger-pc --unattended --runasservice
if errorlevel 1 goto :configfail

echo.
echo  ---- telling Claude the runner is ready ----------------------------
REM  The loop watches for this marker landing on the branch and flips
REM  the build workflow onto this machine by itself - nothing more for
REM  you to do. If the push fails (no saved credentials in this
REM  window), just tell Claude "runner is ready" in the chat instead.
if exist "%REPO%\.git" (
  pushd "%REPO%"
  git pull origin "%BRANCH%" >nul 2>&1
  if not exist tools\runner mkdir tools\runner
  > tools\runner\READY.txt echo runner ledger-pc registered on %COMPUTERNAME% at %DATE% %TIME%
  git add tools\runner\READY.txt >nul 2>&1
  git commit -m "Build runner registered on Jafar's PC" >nul 2>&1
  git push origin HEAD:"%BRANCH%" >nul 2>&1 && echo   Sent - Claude takes it from here.
  popd
) else (
  echo   Project folder not found - tell Claude "runner is ready" in chat.
)

echo.
echo  DONE. The first build on this PC installs Unity by itself
echo  (one-time, a few minutes); after that, builds take roughly
echo  6-10 minutes instead of ~28. Builds only run while this PC is
echo  on - if it is off, they queue until it returns.
echo.
pause
exit /b 0

:downloadfail
echo.
echo  The download FAILED - the reason is above. Check the internet
echo  connection and run this again.
echo.
pause & exit /b 1

:unpackfail
echo.
echo  Unpacking FAILED - the reason is above.
echo.
pause & exit /b 1

:configfail
echo.
echo  Registration FAILED - the reason is above. The commonest causes:
echo  the token expired (get a fresh one from the same page) or this
echo  window is not running as administrator.
echo.
pause & exit /b 1
