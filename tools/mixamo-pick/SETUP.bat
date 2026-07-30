@echo off
setlocal
title LEDGER - setup

REM ===================================================================
REM  START HERE. This is the only file you need to download.
REM
REM  It puts the project on your PC, or updates it if it is already
REM  there, then hands over to the Mixamo harvest.
REM
REM  NO PARENTHESISED IF/ELSE BLOCKS BELOW, and that is deliberate.
REM  The first version had
REM      echo  (fetch failed, carrying on with what is here)
REM  inside an `if exist (...)` block. The `)` in the message text
REM  CLOSED THE BLOCK, so the else branch ran unconditionally: it
REM  updated the repo correctly and then tried to clone on top of it.
REM  Labels and gotos cannot fail that way.
REM ===================================================================

set "REPO=%USERPROFILE%\wc26-picks"
set "BRANCH=claude/game-dev-ai-automation-2h67ix"

echo.
echo  LEDGER - setup
echo  ==============
echo.

where git >nul 2>nul
if errorlevel 1 goto :nogit
where python >nul 2>nul
if errorlevel 1 goto :nopython

if exist "%REPO%\.git" goto :update
goto :clone

:nogit
echo  Git is not installed - it is what copies the project down.
echo.
echo  Get it from https://git-scm.com/downloads
echo  Click through the installer with all the defaults; they are fine.
echo  Then run this file again.
echo.
pause & exit /b 1

:nopython
echo  Python is not installed.
echo.
echo  Get it from https://python.org/downloads
echo  On the installer's FIRST screen tick "Add python.exe to PATH".
echo  That tickbox is easy to miss and nothing works without it.
echo  Then run this file again.
echo.
pause & exit /b 1

:update
echo  Project already at %REPO% - updating it.
pushd "%REPO%"
git fetch origin
if errorlevel 1 echo  Fetch failed - carrying on with the copy already here.
git checkout "%BRANCH%" 2>nul
if errorlevel 1 git checkout -b "%BRANCH%" "origin/%BRANCH%"
git pull origin "%BRANCH%"
popd
goto :ready

:clone
echo  Copying the project to %REPO% ...
echo.
echo  A GitHub sign-in window may appear. That is normal - it is your
echo  own account, and it is how git proves you may read the project.
echo.
git clone --branch "%BRANCH%" https://github.com/jsab258/wc26-picks.git "%REPO%"
if errorlevel 1 goto :clonefailed
goto :ready

:clonefailed
echo.
echo  That did not work. The usual cause is the sign-in being
echo  cancelled or timing out. Run this file again and complete it.
echo.
echo  If it keeps failing, tell me what it printed and I will sort it.
pause & exit /b 1

:ready
if not exist "%REPO%\tools\mixamo-pick\GO.bat" goto :missing
echo.
echo  ------------------------------------------------------------
echo   Project is at %REPO%
echo   Starting the Mixamo harvest now.
echo  ------------------------------------------------------------
echo.
pause
call "%REPO%\tools\mixamo-pick\GO.bat"
exit /b 0

:missing
echo  The project is there but GO.bat is not where I expected.
echo  Tell me and I will sort it.
pause & exit /b 1
