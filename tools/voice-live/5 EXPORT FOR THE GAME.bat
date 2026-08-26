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

title LEDGER - export the graph the game drives
REM ===================================================================
REM  THE GRAPH WE HAVE TAKES THE WRONG THING.
REM
REM  The first export answered "can this model be converted at all".
REM  It can: the transformer agrees with the original to seven decimal
REM  places. That question is closed.
REM
REM  Writing the game's side of it found a different problem. The
REM  converted graph takes an EMBEDDING - the model's internal
REM  representation of a word-piece - and the game has a TOKEN, which
REM  is a number. Converting between them needs two lookup tables that
REM  live inside the model and are not in the exported file.
REM
REM  So the game would have to ship 50 MB of the model's own weights
REM  and redo a piece of the model itself. That is exactly the kind of
REM  thing that has gone wrong twice already here: both times the
REM  result was speech that sounded fine and was subtly wrong, with no
REM  error anywhere to catch it.
REM
REM  This exports a graph that takes the token directly. The lookup
REM  happens inside, where the weights already are, and the game hands
REM  over two numbers and nothing else.
REM
REM  THREE GRAPHS NOW, and the run ends by checking all three and
REM  sending me the result itself - there is nothing for you to copy.
REM
REM    one reads the sentence and the character's voice
REM    one says it a piece at a time
REM    one turns those pieces into sound you can hear
REM
REM  The second and third were added because writing the game's side
REM  kept finding another thing the model does that the game cannot.
REM  Each time the answer is the same: do it inside, where the weights
REM  already are, and hand the game back something simple.
REM
REM  ALREADY CHECKED WITHOUT YOUR HARDWARE, against a real model built
REM  small - same code, same wiring, 6 million weights instead of 520
REM  million, because converting does not care how big a number is. It
REM  agreed to seven decimal places, including at four positions in a
REM  sentence it was never shown. That last part is the one that
REM  matters: get it wrong and every word after the first is placed
REM  wrongly, and it still sounds like speech.
REM
REM  What this run adds is the real weights.
REM
REM  It takes longer than the last one - three exports rather than one,
REM  and the model loads once for each.
REM ===================================================================

if defined LEDGER_GAMEEXPORT_FROMTEMP goto :begin
set "LEDGER_GAMEEXPORT_FROMTEMP=1"
copy /y "%~f0" "%TEMP%\ledger-gameexport.bat" >nul
"%TEMP%\ledger-gameexport.bat" %*
exit /b %errorlevel%
:begin

set "REPO=%USERPROFILE%\wc26-picks"
set "TOOL=%REPO%\tools\voice-live"
set "ENVDIR=%TOOL%\env-export"
set "BRANCH=claude/game-dev-ai-automation-2h67ix"
set "REPORT=%REPO%\game-design\voice-live\export-report.txt"

if not exist "%REPO%\.git" goto :norepo

echo.
echo  LEDGER - export the graph the game drives
echo  =========================================
echo.
echo  Updating...
pushd "%REPO%"
git pull origin "%BRANCH%"
if errorlevel 1 goto :nopull

if not exist "%ENVDIR%\Scripts\python.exe" goto :noenv
set "PY=%ENVDIR%\Scripts\python.exe"
cd /d "%TOOL%"

echo.
echo  ---- exporting -----------------------------------------------------
echo   The model loads first, a minute or two. Then one line runs to shape
echo   the graph against a real memory cache, and the graph is written and
echo   immediately checked against the original - including at positions it
echo   was not traced at, which is the failure worth catching.
echo.
"%PY%" export-for-game.py
if errorlevel 1 set "TROUBLE=text export failed"

echo.
echo  ---- and the last piece: sound into a waveform ----------------------
echo   The graphs above decide WHAT to say, one sound at a time. This one
echo   turns those sounds into something you can actually hear. It is the
echo   last part that was still stuck in Python.
echo.
"%PY%" export-decode.py
if errorlevel 1 set "TROUBLE=%TROUBLE% decode export failed"

echo.
REM  THE AUDIT RUNS EVEN WHEN AN EXPORT FAILED, which is the whole point of
REM  it. The old order jumped to the error message the moment anything went
REM  wrong and skipped the audit and the push - so the one run that most
REM  needed to send something back sent nothing, and the answer came by hand.
REM  A failed export still leaves two working graphs and a stamp saying which
REM  step died, and that is a report worth having.
echo.
echo  ---- checking what is there, and sending the answer back -------------
"%PY%" check-graphs.py
set "AUDIT=%errorlevel%"

if exist "%REPORT%" (
  git add "%REPORT%"
  git commit -m "Graph audit from Jafar's machine" >nul 2>&1
  git pull --rebase origin "%BRANCH%" >nul 2>&1
  git push origin HEAD:"%BRANCH%" && echo   Sent - nothing for you to copy.
)
popd

if defined TROUBLE (
  echo.
  echo  ------------------------------------------------------------------
  echo   SOMETHING DID NOT FINISH: %TROUBLE%
  echo   The reason is in the lines above. The audit has been sent either
  echo   way, so I can see how far it got without you copying anything.
  echo  ------------------------------------------------------------------
)

if exist "%TOOL%\game-out" start "" "%TOOL%\game-out"

echo.
echo  ------------------------------------------------------------------
echo   The audit above already sent itself to me. What is worth a look
echo   from you is the export lines: four numbers matter and they come in two
echo   pairs, each one an agreement against something it was NOT set up
echo   with. If either second number is much worse than its first, the
echo   thing got frozen into the file and I need to know before anything
echo   is built on top of it.
echo.
echo    - positions it was not traced at. Frozen means every word after
echo      the first sits at the wrong place in the sentence.
echo    - a VOICE it was not traced with, plus how far apart the two
echo      voices came out. Frozen means all nineteen characters speak
echo      in whichever voice this run happened to load, and "how far
echo      apart" is what tells the two cases apart - agreeing perfectly
echo      is also what one frozen voice compared against itself does.
echo.
echo   Both would sound like fluent speech and neither raises an error.
echo.
echo   The .onnx files stay on your disk for now - about 2 GB and they
echo   do not belong in git. Shipping them with the game is settled;
echo   how they get there is a later problem.
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
echo  first - it builds it and downloads the model.
echo.
pause & exit /b 1


