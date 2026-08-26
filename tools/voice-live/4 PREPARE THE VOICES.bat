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

title LEDGER - prepare the voices
REM ===================================================================
REM  THE TWO THINGS THAT HAVE TO COME OFF YOUR MACHINE.
REM
REM  Everything else is either converted, written in C#, or checked
REM  here. These two cannot be: they need the model's weights, and the
REM  weights are only on a machine that has downloaded them.
REM
REM    1. THE VOCABULARY - 25 KB, the table that turns words into
REM       tokens. It cannot be derived, only copied, and it is the last
REM       piece of the pipeline that has to TRAVEL rather than be
REM       built. Blocked from my end: HuggingFace is 403 through this
REM       container's proxy.
REM
REM    2. EACH CAST MEMBER'S VOICE - computed once, from their
REM       reference clip, and shipped as data. This is what makes the
REM       voice encoder stop mattering: it refuses to run on DirectML
REM       and its graph is frozen at one clip length, and neither is a
REM       problem for something that runs once at build time on any
REM       machine.
REM
REM  Both land in the repository and get committed, so this is the last
REM  time either is needed. A few minutes, most of it loading the model.
REM ===================================================================

if defined LEDGER_PREP_FROMTEMP goto :begin
set "LEDGER_PREP_FROMTEMP=1"
copy /y "%~f0" "%TEMP%\ledger-prep.bat" >nul
"%TEMP%\ledger-prep.bat" %*
exit /b %errorlevel%
:begin

set "REPO=%USERPROFILE%\wc26-picks"
set "TOOL=%REPO%\tools\voice-live"
set "ENVDIR=%TOOL%\env-export"
set "BRANCH=claude/game-dev-ai-automation-2h67ix"

if not exist "%REPO%\.git" goto :norepo

echo.
echo  LEDGER - prepare the voices
echo  ===========================
echo.
echo  Updating...
pushd "%REPO%"
git pull origin "%BRANCH%"
if errorlevel 1 goto :nopull
popd

if not exist "%ENVDIR%\Scripts\python.exe" goto :noenv
set "PY=%ENVDIR%\Scripts\python.exe"
cd /d "%TOOL%"

echo.
echo  ---- 1 of 2: every cast member's voice, computed once -------------
echo   Loads the model, then reads each reference clip. The vocabulary
echo   comes along with it.
echo.
"%PY%" precompute-voices.py %*
if errorlevel 2 goto :noimport
if errorlevel 1 goto :failed

echo.
echo  ---- 2 of 2: committing them ---------------------------------------
echo   These are inputs to the game, not scratch output, so they belong
echo   in the repository rather than only on this disk.
echo.
pushd "%REPO%"
git add game-design/voice-conds tools/voice-live/tokenizer.json
git commit -m "Voice conditioning and the tokeniser vocabulary, computed on Jafar's machine" 2>nul
if errorlevel 1 echo   (nothing new to commit - they were already there)
git push origin "%BRANCH%"
if errorlevel 1 goto :nopush
popd

echo.
echo  ------------------------------------------------------------------
echo   Done, and this is the last time either of these is needed. From
echo   here the remaining work is the Unity side, which is mine.
echo  ------------------------------------------------------------------
echo.
pause
exit /b 0

:norepo
echo. & echo  No project at %REPO% & echo.
pause & exit /b 1

:nopull
popd
echo. & echo  The pull failed, so nothing ran. The reason is above. & echo.
pause & exit /b 1

:nopush
popd
echo.
echo  The files were computed but the PUSH failed - the reason is above.
echo  They are on your disk and committed locally, so nothing is lost;
echo  send me those lines and we will get them up.
echo.
pause & exit /b 1

:noenv
echo.
echo  The export environment is not there yet. Run "2 TRY THE EXPORT.bat"
echo  first - it builds it and downloads the model.
echo.
pause & exit /b 1

:noimport
echo.
echo  The model would not load, so nothing was computed. That is an
echo  environment answer rather than a model one - send me the line above.
echo.
pause & exit /b 2

:failed
echo.
echo  It ran but produced nothing - the reason is above. Send me those
echo  lines.
echo.
pause & exit /b 1
