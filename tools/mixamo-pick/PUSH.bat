@echo off
setlocal
title LEDGER - push the Mixamo drop
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
REM  Commits and pushes the picked clips. Separate from GO.bat because
REM  a two-hour harvest should not have to be repeated to retry a push.
REM ===================================================================

set "BRANCH=claude/game-dev-ai-automation-2h67ix"

REM  WHAT TO PUSH. Defaults to the Mixamo drop, but the voice installer sets
REM  these before calling so the same tested push serves both. Passed by
REM  environment rather than as arguments, because %1 is already the
REM  --fromtemp flag the TEMP relaunch uses.
if not defined LEDGER_PUSH_PATH set "LEDGER_PUSH_PATH=ledger/Assets/Characters"
if not defined LEDGER_PUSH_MSG set "LEDGER_PUSH_MSG=Mixamo drop: X Bot and Y Bot animation clips"
set "REPO=%USERPROFILE%\wc26-picks"

echo.
echo  LEDGER - pushing the Mixamo drop
echo  ================================
echo.
echo  Repo: %REPO%
echo  Path: %LEDGER_PUSH_PATH%
pushd "%REPO%"

REM ---- who is committing ------------------------------------------
REM  git refuses to commit without an identity, and the first run hit
REM  exactly that: "Author identity unknown". It is a one-time setting.
for /f "delims=" %%E in ('git config user.email 2^>nul') do set "GITEMAIL=%%E"
if not "%GITEMAIL%"=="" goto :haveidentity

echo.
echo  git does not know who you are on this machine yet - it refuses to
echo  make a commit without a name and an email. One-time setting.
echo.
echo  Press Enter to use the defaults shown, or type something else.
echo.
set "NEWNAME=Jafar Sabadia"
set /p NEWNAME=  Name  [%NEWNAME%]: 
set "NEWMAIL=jafar.sabadia@bluewin.ch"
echo.
echo  If you would rather your email did not appear in public commits,
echo  GitHub gives you a private one: Settings - Emails - "Keep my email
echo  addresses private", then use the ...@users.noreply.github.com
echo  address it shows you.
echo.
set /p NEWMAIL=  Email [%NEWMAIL%]: 
git config --global user.name "%NEWNAME%"
git config --global user.email "%NEWMAIL%"
echo.
echo  Set. git will remember this for every project from now on.
:haveidentity
for /f "delims=" %%E in ('git config user.email 2^>nul') do set "GITEMAIL=%%E"
echo  Committing as %GITEMAIL%
echo.

REM ---- commit ------------------------------------------------------
git add "%LEDGER_PUSH_PATH%"
git diff --cached --quiet
if errorlevel 1 goto :docommit
echo  Nothing staged under %LEDGER_PUSH_PATH% - trying the push anyway.
goto :dopush

:docommit
git commit -m "%LEDGER_PUSH_MSG%"
if errorlevel 1 goto :commitfailed
echo  Committed.

:dopush
REM  Rebase first: the remote will have moved on while the harvest ran.
git pull --rebase origin "%BRANCH%"
if errorlevel 1 goto :rebasefailed
git push origin HEAD:%BRANCH%
if errorlevel 1 goto :pushfailed

echo.
echo  ==================================================================
echo   Pushed. The clips are on GitHub - I can see them now.
echo  ==================================================================
popd & pause & exit /b 0

:commitfailed
echo.
echo  The commit failed - the reason is just above. Nothing is lost; the
echo  clips are still in ledger\Assets\Characters. Send me that message.
popd & pause & exit /b 1

:rebasefailed
echo.
echo  The rebase hit a snag. Nothing is lost. Send me the output above.
popd & pause & exit /b 1

:pushfailed
echo.
echo  The push failed - the reason is just above. The commit is safely on
echo  your machine, so this is only about getting it to GitHub. Send me
echo  that message.
popd & pause & exit /b 1
