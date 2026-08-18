@echo off
setlocal
title LEDGER - ten more bodies
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
REM  TEN MORE BODIES. Double-click it. There is nothing to type.
REM
REM  WHY THESE TEN. Picked from the account's REAL catalogue for the
REM  first time - 108 names, listed by LIST-BODIES.bat - rather than
REM  from a memory of what Mixamo probably has. Roughly half the
REM  catalogue is fantasy, horror, sci-fi or medieval (Goblin,
REM  Warzombie, Paladin, Pumpkinhulk, Peasant Girl, Swat, Exo Red);
REM  that half is reliably rejectable from the NAME. These ten come out
REM  of what is left, which is Mixamo's ordinary-people set.
REM
REM  The pool is 2 men and 4 women today (Joe, Remy / Martha, Michelle,
REM  Sophie, Sporty Granny), so this is six men and four women and
REM  lands at 8/8.
REM
REM  WHAT A NAME CANNOT TELL ANYBODY is whether a model is old, heavy or
REM  stylised. That is exactly how The Boss (5.11 heads) and Big Vegas
REM  (6.05) got onto the street and had to be taken off again. So this
REM  is a shortlist, not a decision, and the next step is the point:
REM
REM  IT MEASURES BEFORE IT COMMITS. Git keeps a file for ever even after
REM  you delete it, so a bad 50MB body committed is 50MB carried for
REM  good. Measured first, a bad one costs nothing to drop.
REM
REM  Anything already downloaded is SKIPPED. Free either way - Mixamo
REM  characters are a download, not a purchase.
REM ===================================================================

set "MH=%USERPROFILE%\ledger-mixamo\MixamoHarvester"
set "REPO=%USERPROFILE%\wc26-picks"
set "SCRIPTS=%REPO%\tools\mixamo-pick"
set "CHARS=%REPO%\ledger\Assets\Characters"
set "BRANCH=claude/game-dev-ai-automation-2h67ix"
set "WANT=abe,adam,david,james,leonard,pete,claire,elizabeth,kate,shannon"

echo.
echo  LEDGER - ten more bodies
echo  ========================
echo.
echo  Fetching: %WANT%
echo  Anything already on disk is skipped.
echo.

if not exist "%MH%\mixamo_token.txt" goto :notoken

echo  [1/4] Updating the project...
pushd "%REPO%"
git pull origin "%BRANCH%"
if errorlevel 1 echo  Pull failed - carrying on with what is here.
popd
echo.

echo  [2/4] Downloading bodies with skin...
echo.
python "%SCRIPTS%\fetch_bodies.py" --harvester "%MH%" --out "%CHARS%" --names "%WANT%"
if errorlevel 1 goto :failed
echo.

echo  [3/4] Measuring what arrived...
echo.
REM  ONLY PRINTS. Nothing is auto-deleted: a script that throws away a
REM  download it has just made is the shape of fault that destroyed 24
REM  listened-to voice clips in July. The measuring is automatic; the
REM  deleting stays a person's decision.
python "%REPO%\tools\body-proportions.py"
echo.
echo  ---------------------------------------------------------------
echo   COPY THE TABLE ABOVE INTO THE CHAT.
echo   Under about 7 heads is a caricature and should come back out -
echo   and right now dropping one is free, because nothing is committed
echo   yet. Press a key to commit, or close this window to stop here.
echo  ---------------------------------------------------------------
echo.
pause

echo  [4/4] Committing...
pushd "%REPO%"
git add "ledger/Assets/Characters"
git commit -m "Ten more character bodies, picked from the real catalogue"
if errorlevel 1 echo  Nothing new to commit.
git push origin "%BRANCH%"
if errorlevel 1 echo  Push failed - run PUSH.bat later, the files are safe on disk.
popd

echo.
echo  Done. Paste the table into the chat and the caricatures come out
echo  in the next commit.
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
