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

title LEDGER - hear it speak
REM ===================================================================
REM  THE FIRST THING IN THIS WHOLE EFFORT YOU CAN LISTEN TO.
REM
REM  Everything so far has been numbers: the transformer matches the
REM  original to seven decimal places, the vocoder to six, the sampler
REM  to five. None of that answers the question that actually matters -
REM  does the loop rebuilt for the game produce speech a person would
REM  accept? A pipeline can be right at every join and still sound
REM  wrong, and no measurement would say so.
REM
REM  This writes TWO wav files from the same voice and the same words:
REM
REM     model.wav   chatterbox's own code, untouched - the CONTROL
REM     ours.wav    the same line through the loop the game will run
REM
REM  BOTH, ALWAYS. One file on its own cannot be judged - this model
REM  has bad days on any given line, so a mediocre take would read as
REM  a broken loop and a good one would prove nothing. Two files turn
REM  it into "do these sound like the same person doing the same job",
REM  which an ear settles in five seconds.
REM
REM  It uses the same environment the export probe built. Nothing is
REM  downloaded that is not already there.
REM ===================================================================

REM  THE RELAUNCH MARKER IS AN ENVIRONMENT VARIABLE, NOT AN ARGUMENT.
REM
REM  It was `--fromtemp` as an argument, and this bat forwards %* to
REM  speak.py so a user's --text reaches it. %* in cmd is ALWAYS the
REM  original argument list - `shift` does not change it - so the
REM  marker went to Python too and argparse refused the lot:
REM  "unrecognized arguments: --fromtemp". A child process inherits
REM  the environment, so a variable carries the same signal and leaves
REM  %* holding only what the user typed.
if defined LEDGER_SPEAK_FROMTEMP goto :begin
set "LEDGER_SPEAK_FROMTEMP=1"
copy /y "%~f0" "%TEMP%\ledger-speak.bat" >nul
"%TEMP%\ledger-speak.bat" %*
exit /b %errorlevel%
:begin

set "REPO=%USERPROFILE%\wc26-picks"
set "TOOL=%REPO%\tools\voice-live"
set "ENVDIR=%TOOL%\env-export"
set "BRANCH=claude/game-dev-ai-automation-2h67ix"

if not exist "%REPO%\.git" goto :norepo

echo.
echo  LEDGER - hear it speak
echo  ======================
echo.
echo  Updating...
pushd "%REPO%"
git pull origin "%BRANCH%"
if errorlevel 1 goto :nopull
popd

if not exist "%ENVDIR%\Scripts\python.exe" goto :noenv
set "PY=%ENVDIR%\Scripts\python.exe"
cd /d "%TOOL%"

REM  soundfile writes the wav files. Checked on its own rather than
REM  inside a first-time-install block, because the environment already
REM  exists - the same trap that made three runs report a missing
REM  onnxscript while the install line sat in a block that never ran.
"%PY%" -c "import soundfile" >nul 2>nul
if errorlevel 1 (
  echo  Installing soundfile, which writes the wav files...
  "%PY%" -m pip install soundfile
  if errorlevel 1 goto :noinstall
)

echo.
echo  ---- speaking ------------------------------------------------------
echo   The model loads first, which takes a minute or two. Then two
echo   takes of the same line: the model's own, and ours.
echo.
"%PY%" speak.py %*
if errorlevel 2 goto :noimport
if errorlevel 1 goto :failed

if exist "%TOOL%\speak-out" start "" "%TOOL%\speak-out"

echo.
echo  ------------------------------------------------------------------
echo   Play BOTH files. The question is not whether it is a good take -
echo   this model has bad days on any line. It is whether the two sound
echo   like the SAME PERSON doing the SAME JOB.
echo.
echo     they match          the loop the game runs is right, and what
echo                         is left is plumbing
echo     ours is worse       the loop or the sampler is wrong, and the
echo                         difference tells me which
echo     BOTH are poor       the model is having a bad line - run it
echo                         again with different words before we
echo                         conclude anything
echo.
echo   To try your own line, or another cast member:
echo     "3 HEAR IT SPEAK.bat" --text "whatever you want him to say"
echo     "3 HEAR IT SPEAK.bat" --voice lena --text "not tonight"
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

:noenv
echo.
echo  The export environment is not there yet. Run "2 TRY THE EXPORT.bat"
echo  first - it builds it and downloads the model. This one reuses it
echo  rather than building a second copy of several GB.
echo.
pause & exit /b 1

:noinstall
echo. & echo  The install FAILED - the reason is above. Send me those lines. & echo.
pause & exit /b 1

:noimport
echo.
echo  The model would not load, so nothing was spoken. That is an
echo  environment answer rather than a model one - send me the line above.
echo.
pause & exit /b 2

:failed
echo.
echo  It ran but produced nothing - the reason is above. Send me those
echo  lines. A loop that stops at once, or with no acoustic tokens, is a
echo  real result and tells me where to look.
echo.
pause & exit /b 1
