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

title LEDGER - halve the graphs, time them again
REM ===================================================================
REM  RUN FROM A COPY. This script pulls, and a pull can rewrite THIS FILE
REM  while cmd.exe is still reading it by byte offset.
REM ===================================================================
if /i "%~1"=="--fromtemp" goto :begin
copy /y "%~f0" "%TEMP%\ledger-faster.bat" >nul
"%TEMP%\ledger-faster.bat" --fromtemp
exit /b %errorlevel%
:begin

REM ===================================================================
REM  WHY THIS EXISTS. The timing run read 1.7x real time: the card
REM  makes speech tokens at about 21 a second and the mouth spends 25.
REM  The game already contains the machinery to start a line playing
REM  while the rest is still being made - it switches itself on the
REM  moment the token rate beats the mouth. This converts the two text
REM  graphs to half precision, which the step probe's own numbers say
REM  should roughly double the rate, then times them again. The number
REM  it prints decides the next step; nothing here changes the game.
REM
REM  Afterwards, "3 HEAR IT SPEAK.bat" is the ears check - half
REM  precision is safe arithmetic on paper and still has to sound
REM  like the street.
REM ===================================================================

set "REPO=%USERPROFILE%\wc26-picks"
set "TOOL=%REPO%\tools\voice-live"
set "ENVDIR=%TOOL%\env-export"
set "BRANCH=claude/game-dev-ai-automation-2h67ix"
set "REPORT=%REPO%\game-design\voice-live\speed-report.txt"

if not exist "%REPO%\.git" goto :norepo
echo.
echo  LEDGER - halve the graphs, time them again
echo  ==========================================
echo.
pushd "%REPO%"
git pull origin "%BRANCH%"
if errorlevel 1 goto :nopull
if not exist "%ENVDIR%\Scripts\python.exe" goto :noenv

echo.
echo  ---- converting (a few minutes, needs no attention) -----------------
"%ENVDIR%\Scripts\python.exe" "%TOOL%\convert-fp16.py"
if errorlevel 1 goto :failed

echo.
echo  ---- timing the halves ----------------------------------------------
"%ENVDIR%\Scripts\python.exe" "%TOOL%\time-a-line.py" --fp16

echo.
if exist "%REPORT%" (
  git add "%REPORT%"
  git commit -m "Half-precision timing from Jafar's machine" >nul 2>&1
  git pull --rebase origin "%BRANCH%" >nul 2>&1
  git push origin HEAD:"%BRANCH%" && echo   Sent - nothing for you to copy.
)
popd
echo.
echo  If the new "x real time" is at or under about 1.0, characters can
echo  speak as fast as people talk. Run "3 HEAR IT SPEAK.bat" once to
echo  check the halves still SOUND right.
echo.
pause
exit /b 0

:failed
popd
echo.
echo  The conversion FAILED - the reason is above, in full. Nothing was
echo  changed: the full-precision graphs are untouched on disk.
echo.
pause & exit /b 1

:nopull
popd
echo. & echo  The pull failed, so nothing ran. The reason is above. & echo.
pause & exit /b 1

:noenv
popd
echo. & echo  No export environment - run "2 TRY THE EXPORT.bat" first. & echo.
pause & exit /b 1

:norepo
echo. & echo  No project at %REPO% & echo.
pause & exit /b 1
