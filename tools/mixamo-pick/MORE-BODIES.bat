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

title LEDGER - five more character bodies
cd /d "%~dp0"

REM ===================================================================
REM  RUN FROM A COPY. This script pulls, and a pull can rewrite THIS FILE
REM  while cmd.exe is still reading it by byte offset - which produced
REM  'nloads' is not recognized, the tail of a URL, from a script that had
REM  been replaced underneath itself mid-run.
REM ===================================================================
if /i "%~1"=="--fromtemp" goto :begin
copy /y "%~f0" "%TEMP%\ledger-%~n0.bat" >nul
"%TEMP%\ledger-%~n0.bat" --fromtemp
exit /b %errorlevel%
:begin

REM ===================================================================
REM  FIVE MORE BODIES. Double-click it; there is nothing to type.
REM
REM  The first run got Michelle, Remy and Sophie. The fourth default,
REM  "shae", is not in this account's catalogue - so the rest have to be
REM  named by hand, and these five are named below.
REM
REM  WHY THESE FIVE. Three young slim bodies is the narrowest silhouette
REM  range there is, and silhouette is what reads at street distance in
REM  fog. The Boss is a man who looks like he runs an outfit, which the
REM  game has and nobody looks like. Sporty Granny is the only older
REM  person in the catalogue and age is a bigger visual difference than
REM  clothing. Big Vegas is a heavy build, which nothing else gives.
REM  Joe and Martha thin out the repetition across sixty characters.
REM
REM  CHOSEN FROM NAMES, NOT FROM LOOKING - nobody here can see these
REM  models. Two or three may be stylised or wrong for a late-analog
REM  port city. That is expected: they land in the next build's stills
REM  and whatever does not fit gets deleted. Cheaper to look than guess.
REM
REM  Anything already downloaded is SKIPPED, so this costs only what is
REM  actually new. Free - Mixamo characters are a download, not a
REM  purchase.
REM ===================================================================

set "MH=%USERPROFILE%\ledger-mixamo\MixamoHarvester"
set "REPO=%USERPROFILE%\wc26-picks"
set "SCRIPTS=%REPO%\tools\mixamo-pick"
set "CHARS=%REPO%\ledger\Assets\Characters"
set "BRANCH=claude/game-dev-ai-automation-2h67ix"
set "WANT=the boss,sporty granny,big vegas,joe,martha"

echo.
echo  LEDGER - five more character bodies
echo  ==================================
echo.
echo  Fetching: %WANT%
echo  Anything already on disk is skipped.
echo.

if not exist "%MH%\mixamo_token.txt" goto :notoken

echo  [1/3] Updating the project...
pushd "%REPO%"
git pull origin "%BRANCH%"
if errorlevel 1 echo  Pull failed - carrying on with what is here.
popd
echo.

echo  [2/3] Downloading bodies with skin...
echo.
python "%SCRIPTS%\fetch_bodies.py" --harvester "%MH%" --out "%CHARS%" --names "%WANT%"
if errorlevel 1 goto :failed
echo.

echo  [3/3] Committing...
pushd "%REPO%"
git add "ledger/Assets/Characters"
git commit -m "Five more character bodies from Mixamo, with skin"
if errorlevel 1 echo  Nothing new to commit.
git push origin "%BRANCH%"
if errorlevel 1 echo  Push failed - run PUSH.bat later, the files are safe on disk.
popd

echo.
echo  Done. Tell Claude they have landed and the next build will show them.
echo.
echo  If a name came back "not in this account's catalogue", that one does
echo  not exist under that spelling - the list it printed is the truth and
echo  the fix is one word in this file.
echo.
pause
exit /b 0

:notoken
echo  No Mixamo token found at:
echo      %MH%\mixamo_token.txt
echo.
echo  Tokens are short-lived. Get a fresh one:
echo      1. open mixamo.com and sign in
echo      2. press F12 for the console
echo      3. run:  localStorage.getItem^('access_token'^)
echo      4. paste it into that file, without the quotes
echo.
pause
exit /b 2

:failed
echo.
echo  The download did not complete. The message above says why -
echo  send it over and it gets fixed in one pass rather than three.
echo.
pause
exit /b 1
