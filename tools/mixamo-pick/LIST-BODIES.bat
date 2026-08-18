@echo off
setlocal
title LEDGER - list every Mixamo body this account can see
cd /d "%~dp0"

REM ===================================================================
REM  RUN FROM A COPY. This script pulls, and a pull can rewrite THIS FILE
REM  while cmd.exe is still reading it by byte offset.
REM ===================================================================
if /i "%~1"=="--fromtemp" goto :begin
copy /y "%~f0" "%TEMP%\ledger-%~n0.bat" >nul
"%TEMP%\ledger-%~n0.bat" --fromtemp
exit /b %errorlevel%
:begin

REM ===================================================================
REM  PRINTS THE NAMES. Downloads nothing, changes nothing, costs nothing.
REM
REM  WHY THIS EXISTS. Every body in this game was picked from a GUESS at
REM  a name - MORE-BODIES.bat says so in its own comments: "CHOSEN FROM
REM  NAMES, NOT FROM LOOKING". Two of the five it picked that way turned
REM  out to be caricatures and were taken off the street on 17 Aug, which
REM  is a 40% miss rate paid for in build round trips.
REM
REM  The catalogue was only ever printed when a pick MISSED, and only the
REM  first forty of it. So there was no way to choose from the real list.
REM  Now there is.
REM
REM  Copy the output into the chat. The next pick gets made from names
REM  that exist, and whatever is downloaded gets MEASURED by
REM  tools/body-proportions.py before it can reach the street - so a
REM  caricature is caught here rather than in a screenshot three builds
REM  later.
REM ===================================================================

set "MH=%USERPROFILE%\ledger-mixamo\MixamoHarvester"
set "REPO=%USERPROFILE%\wc26-picks"
set "SCRIPTS=%REPO%\tools\mixamo-pick"
set "BRANCH=claude/game-dev-ai-automation-2h67ix"

echo.
echo  LEDGER - every body this account can see
echo  =======================================
echo.

if not exist "%MH%\mixamo_token.txt" goto :notoken

echo  [1/2] Updating the project...
pushd "%REPO%"
git pull origin "%BRANCH%"
if errorlevel 1 echo  Pull failed - carrying on with what is here.
popd
echo.

echo  [2/2] Asking Mixamo for the list...
echo.
python "%SCRIPTS%\fetch_bodies.py" --harvester "%MH%" --list
if errorlevel 1 goto :failed

echo.
echo  Copy everything above into the chat.
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
echo  That did not work. The message above says why - send it over.
echo.
pause
exit /b 1
