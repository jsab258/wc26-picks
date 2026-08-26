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

title LEDGER - how long does one line take
REM ===================================================================
REM  THE NUMBER THAT DECIDES WHETHER ANY OF THIS SHIPS.
REM
REM  Everything about live speech is now built and checked. None of it
REM  matters if a character takes fifteen seconds to say six words.
REM
REM  The figure quoted so far - about ten seconds - was measured in
REM  Python, on the processor, using a completely different piece of
REM  software from the one the game will use. It was never a
REM  measurement of the game. This is.
REM
REM  It runs the three exported files exactly the way the game will:
REM  read the sentence, produce the sounds one at a time, turn them
REM  into audio. Then it says how long that took against how much
REM  speech came out.
REM
REM  It is quick - no model to load, just the three files - and it
REM  sends its answer back itself.
REM ===================================================================

if defined LEDGER_TIMELINE_FROMTEMP goto :begin
set "LEDGER_TIMELINE_FROMTEMP=1"
copy /y "%~f0" "%TEMP%\ledger-timeline.bat" >nul
"%TEMP%\ledger-timeline.bat" %*
exit /b %errorlevel%
:begin

set "REPO=%USERPROFILE%\wc26-picks"
set "TOOL=%REPO%\tools\voice-live"
set "ENVDIR=%TOOL%\env-export"
set "BRANCH=claude/game-dev-ai-automation-2h67ix"
set "REPORT=%REPO%\game-design\voice-live\speed-report.txt"

if not exist "%REPO%\.git" goto :norepo
echo.
echo  LEDGER - how long does one line take
echo  ====================================
echo.
pushd "%REPO%"
git pull origin "%BRANCH%"
if errorlevel 1 goto :nopull
if not exist "%ENVDIR%\Scripts\python.exe" goto :noenv

echo.
echo  ---- timing ---------------------------------------------------------
"%ENVDIR%\Scripts\python.exe" "%TOOL%\time-a-line.py"

echo.
if exist "%REPORT%" (
  git add "%REPORT%"
  git commit -m "Line timing from Jafar's machine" >nul 2>&1
  git pull --rebase origin "%BRANCH%" >nul 2>&1
  git push origin HEAD:"%BRANCH%" && echo   Sent - nothing for you to copy.
)
popd
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

:noenv
popd
echo.
echo  The environment is not there yet. Run "2 TRY THE EXPORT.bat" first.
echo.
pause & exit /b 1
