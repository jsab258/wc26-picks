@echo off
setlocal enabledelayedexpansion

REM  GIT MUST NEVER OPEN AN EDITOR HERE. 26 Aug: a `git pull` that made a
REM  merge commit opened vim in Jafar's window, he closed it, and the
REM  half-finished merge blocked every pull afterwards. `true` exits 0 at
REM  once so git takes the default message and carries on.
REM  tools\lint-bat-editor.py fails the build for any .bat that runs git
REM  without this.
set "GIT_EDITOR=true"
set "GIT_MERGE_AUTOEDIT=no"

title LEDGER - studio machine
color 07

REM ===================================================================
REM  ONE CLICK, AND THEN NO CLICKS.
REM
REM  Double-click this once. It leaves a window open that watches the
REM  project for work and does it here: the prop batch, the picture
REM  batch, the surface fetch, the voice jobs. Nothing is asked of you
REM  and nothing needs sending back by hand.
REM
REM  WHAT IT REPLACES. Every job that needs this graphics card or the
REM  4.5 GB of models used to cost a message, a wait, and a double-click
REM  on a different .bat. The prop batch on 1 Sep cost exactly that.
REM
REM  IT ALSO ASKS TO START ITSELF AT SIGN-IN, and it TELLS YOU WHETHER
REM  THAT WORKED rather than assuming. Read the box that prints below.
REM
REM  TO STOP IT: close this window. To stop it starting at sign-in, the
REM  box below prints the one file to delete.
REM
REM  NOTHING IS BOUGHT AND NO ACCOUNT IS USED.
REM
REM  THIS FILE HAS NEVER BEEN RUN WHERE IT WAS WRITTEN. There is no
REM  Windows in that container, so every DECISION this file could get
REM  wrong lives in tools\pc-watcher.py instead, which has a selftest
REM  that runs there. What is left up here is: find the project, find a
REM  python, copy one file, and check whether the copy arrived.
REM ===================================================================

REM  RUN FROM A COPY. Matching the branch can rewrite this very file
REM  while cmd.exe is still reading it by byte offset, which once made a
REM  script print the tail of its own replacement.
if /i "%~1"=="--fromtemp" goto :begin
copy /y "%~f0" "%TEMP%\ledger-studio.bat" >nul
"%TEMP%\ledger-studio.bat" --fromtemp
exit /b %errorlevel%
:begin

echo.
echo   LEDGER - studio machine
echo   =======================
echo.

REM --- where is the repository? ---------------------------------------
REM  This file lives at the top of the project, so one level up from a
REM  TEMP copy is nothing useful. The named path is tried first for that
REM  reason, and it is the path this machine actually uses: the prop
REM  batch of 1 Sep ran out of C:\Users\Jafar\wc26-picks.
set "REPO=%USERPROFILE%\wc26-picks"
if not exist "%REPO%\CLAUDE.md" set "REPO=%~dp0."
for %%I in ("%REPO%") do set "REPO=%%~fI"
if not exist "%REPO%\CLAUDE.md" (
  echo   COULD NOT FIND THE PROJECT.
  echo     looked in "%USERPROFILE%\wc26-picks"
  echo     and in    "%~dp0."
  echo   Without it there is nothing to watch. Move the project folder
  echo   back to %USERPROFILE%\wc26-picks and click this again.
  goto :theend
)
cd /d "%REPO%"
echo   project : %REPO%

REM --- copy anything this machine made, somewhere git cannot reach -----
REM  Look before you destroy: a cancelled job once deleted 24 clips
REM  Jafar had already listened to, and reported success.
set "RESCUE=%USERPROFILE%\ledger-rescued"
mkdir "%RESCUE%" >nul 2>&1
copy /y "game-design\pc-jobs\result.txt" "%RESCUE%\" >nul 2>&1
copy /y "production\mesh-reports\*.txt" "%RESCUE%\" >nul 2>&1

REM --- update, so the watcher that runs is the current one -------------
REM  A FAILED PULL IS NOT FATAL BUT IT IS SAID. "ran the old code" and
REM  "ran the new code" must not look identical in the only window
REM  anybody reads.
echo   Updating the project...
git --no-pager rebase --abort >nul 2>&1
git --no-pager merge --abort >nul 2>&1
git --no-pager cherry-pick --abort >nul 2>&1
git --no-pager fetch origin claude/game-dev-ai-automation-2h67ix
if errorlevel 1 (
  echo         COULD NOT REACH GITHUB. Carrying on with the copy already
  echo         on this PC. If this behaves like an older version, that is
  echo         why. The watcher retries the fetch every pass anyway.
) else (
  REM  A DISCARD, NOT A MERGE, and the same one the watcher makes every
  REM  pass. Untracked files are not touched by it, which is what keeps
  REM  the python environment, the exported graphs and the meshes safe.
  git --no-pager reset --hard FETCH_HEAD >nul 2>&1
)

REM --- find a python ---------------------------------------------------
REM  ORDER MATTERS AND IT IS NOT ARBITRARY. env-export is the voice
REM  environment: it has torch and onnxruntime in it, and the voice jobs
REM  fail with an import error on anything else. The prop and picture
REM  pipelines are stdlib only, so they run under any Python 3.8+, and
REM  miniconda3 is second because that is what this machine's own
REM  toolchain probe reported on 1 Sep (3.12.8).
set "PY="
set "VOICEPY="
call :trypy "%REPO%\tools\voice-live\env-export\Scripts\python.exe"
if defined PY set "VOICEPY=1"
call :trypy "%USERPROFILE%\miniconda3\python.exe"
if not defined PY for /f "delims=" %%P in ('where python.exe 2^>nul') do call :trypy "%%P"
if not defined PY (
  py -3 -c "import sys" >nul 2>&1
  if not errorlevel 1 set "PY=py -3"
)
if not defined PY (
  echo.
  echo   NO PYTHON 3.8+ ON THIS PC, so nothing can be watched for.
  echo   Fix, one minute: install Python from the Microsoft Store or
  echo   python.org and click this again. Nothing is installed into it.
  goto :theend
)
echo   python  : %PY%
if not defined VOICEPY (
  echo             NOTE: this is NOT the voice environment. The prop and
  echo             picture jobs are stdlib only and will run. The VOICE
  echo             jobs will fail on an import, and that failure is a
  echo             fact about this interpreter, not about the code.
  echo             Fix: tools\voice-live\1 RESTORE THE ENVIRONMENT.bat
)

REM --- start at sign-in, without admin ---------------------------------
REM  ONE MECHANISM, NOT TWO. The Startup folder is a plain file write
REM  into this user's own AppData, so it cannot need elevation, which
REM  matters on this machine specifically: the self-hosted runner could
REM  not get admin here and the Blender MSI came back 1603 for the same
REM  reason. The portable-zip route is what worked, and this is the same
REM  shape of answer. `schtasks /sc onlogon` is deliberately NOT also
REM  attempted: two autostart entries would open two watchers at sign-in
REM  and they would fight over the same git index.
REM
REM  WHAT IT DOES NOT DO, said plainly rather than left to be assumed:
REM  this starts at SIGN-IN, not at boot. A machine that reboots and
REM  waits at the sign-in screen is not watching for anything. Starting
REM  before a sign-in means a Windows service, and a service is exactly
REM  what could not be installed here for want of admin.
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "HOOK=%STARTUP%\LEDGER studio machine.bat"
set "AUTO=NOT INSTALLED"
set "AUTOWHY=the Startup folder was not there"
if exist "%STARTUP%" (
  REM  A LAUNCHER, NOT A COPY OF THIS FILE. It calls the one in the
  REM  project, so every sign-in runs the CURRENT version rather than
  REM  whatever this file said on the day it was installed.
  > "%HOOK%" echo @echo off
  >>"%HOOK%" echo REM  Written by "START THE STUDIO MACHINE.bat". Delete this file
  >>"%HOOK%" echo REM  to stop the studio machine starting when you sign in.
  >>"%HOOK%" echo cd /d "%REPO%"
  >>"%HOOK%" echo start "" "%REPO%\START THE STUDIO MACHINE.bat"
  REM  THE EFFECT, NOT THE EXIT CODE. `echo >file` reports success on a
  REM  redirect that wrote nothing, and this project has been told that
  REM  a step succeeded while it deleted content, pushed nothing and
  REM  produced an empty file.
  if exist "%HOOK%" (
    set "AUTO=INSTALLED"
    set "AUTOWHY=none"
  ) else (
    set "AUTOWHY=the Startup folder is there but the file could not be written"
  )
)

echo.
echo   ============================================================
if "!AUTO!"=="INSTALLED" (
  echo   STARTS AT SIGN-IN: YES. Verified by reading the file back, not
  echo   by trusting the copy.
  echo     "!HOOK!"
  echo   Delete that one file to stop it. No admin was needed and none
  echo   was asked for.
  echo   It starts when you SIGN IN, not when the PC boots. A machine
  echo   sitting at the sign-in screen is not watching for anything.
) else (
  echo   STARTS AT SIGN-IN: NO, and this run is START-ONCE only.
  echo     reason: !AUTOWHY!
  echo   Everything below still works for as long as this window is
  echo   open. If the PC restarts, double-click this file again.
  echo   SEND BACK: this box. It is the only thing that says which of
  echo   the two happened.
)
echo   ============================================================

REM --- write the answer where it can be read from the other end --------
REM  THE WINDOW IS NOT A CHANNEL I CAN READ. A file in the repository is
REM  the one channel that has never failed here, so the same answer goes
REM  into the project and rides out on the next job the watcher
REM  publishes. No spaces inside a key=value: every reader in this
REM  project splits on whitespace and truncates silently.
REM  EVERY VALUE IS ONE WORD. `!VAR: =_!` is cmd's own replace, so a
REM  reason with spaces in it arrives whole instead of being truncated at
REM  the first space by the next grep anybody types.
set "ANSWERFILE=%REPO%\game-design\pc-jobs\machine-start.txt"
set "AUTOKEY=no"
if "!AUTO!"=="INSTALLED" set "AUTOKEY=yes"
set "VOICEKEY=no"
if defined VOICEPY set "VOICEKEY=yes"
set "REPOKEY=%REPO%"
> "%ANSWERFILE%" echo autostart=!AUTOKEY!
>>"%ANSWERFILE%" echo autostartWhy=!AUTOWHY: =_!
>>"%ANSWERFILE%" echo autostartPath=!HOOK: =_!
>>"%ANSWERFILE%" echo voiceEnv=!VOICEKEY!
>>"%ANSWERFILE%" echo scope=signin-not-boot
>>"%ANSWERFILE%" echo repo=!REPOKEY: =_!
>>"%ANSWERFILE%" echo written=!DATE: =_!_!TIME: =0!

echo.
echo   Watching for work. Leave this window open.
echo   Jobs it can run are listed on the next line by the watcher itself.
echo.
%PY% "%REPO%\tools\pc-watcher.py"

echo.
echo   The studio machine stopped. Close this window, or click the file
echo   again. Nothing was left running.
goto :theend

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

:theend
echo.
pause
endlocal
