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

title LEDGER - get the character bodies
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
REM  DOWNLOADS THE CHARACTER BODIES. Minutes, not hours - four meshes,
REM  no animation harvest.
REM
REM  The harvest got 42 animations and two bodies, and both bodies are
REM  the grey featureless mannequins Mixamo uses for previews. The
REM  player has been one of them ever since. This gets real people.
REM
REM  Free. Mixamo's characters cost nothing; this is a download, not a
REM  purchase.
REM ===================================================================

set "MH=%USERPROFILE%\ledger-mixamo\MixamoHarvester"
set "REPO=%USERPROFILE%\wc26-picks"
set "SCRIPTS=%REPO%\tools\mixamo-pick"
set "CHARS=%REPO%\ledger\Assets\Characters"
set "BRANCH=claude/game-dev-ai-automation-2h67ix"

echo.
echo  LEDGER - character bodies
echo  =========================
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
REM  OPTIONAL NAMES. `BODIES.bat vanguard` fetches just that one, which is
REM  what the second run needs: three bodies landed and "shae" is not in
REM  this account's catalogue, so the fourth has to be named by hand.
REM  With no argument it behaves exactly as before.
if "%~1"=="" (
  python "%SCRIPTS%\fetch_bodies.py" --harvester "%MH%" --out "%CHARS%"
) else (
  python "%SCRIPTS%\fetch_bodies.py" --harvester "%MH%" --out "%CHARS%" --names "%~1"
)
if errorlevel 1 goto :failed
echo.

echo  [3/4] Measuring what arrived...
echo.
REM  MEASURE BEFORE COMMITTING, because git keeps a file for ever even
REM  after it is deleted. Two of the last five bodies picked from names
REM  were caricatures - The Boss at 5.11 heads, Big Vegas at 6.05 - and
REM  they were only caught once they were in the repo and on the street.
REM  This prints the proportions of everything in Assets/Characters so a
REM  bad one can be deleted while deleting it still costs nothing.
REM
REM  It only PRINTS. Nothing is auto-deleted: a script that throws away a
REM  download it just made is the shape of fault that cost this project
REM  24 listened-to voice clips, and a human reading a table is cheap.
python "%REPO%\tools\body-proportions.py"
echo.
echo  ---------------------------------------------------------------
echo   Paste the table above into the chat BEFORE the commit finishes
echo   mattering - anything under about 7 heads is a caricature and
echo   should come back out.
echo  ---------------------------------------------------------------
echo.
pause

echo  [4/4] Committing...
pushd "%REPO%"
git add "ledger/Assets/Characters"
git commit -m "Character bodies from Mixamo, with skin"
if errorlevel 1 echo  Nothing new to commit.
git push origin "%BRANCH%"
if errorlevel 1 echo  Push failed - run PUSH.bat later, the files are safe on disk.
popd

echo.
echo  Done. The bodies are in the repo.
echo.
echo  Tell Claude they have landed - pointing the game at one is a
echo  one-line change and the next build will show a real person.
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
