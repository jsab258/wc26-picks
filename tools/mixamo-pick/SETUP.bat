@echo off
setlocal
title LEDGER - setup
color 0F

REM ===================================================================
REM  START HERE. This is the only file you need to download.
REM
REM  It puts the project on your PC (or updates it if it is already
REM  there), then hands straight over to the Mixamo harvest.
REM ===================================================================

set "REPO=%USERPROFILE%\wc26-picks"
set "BRANCH=claude/game-dev-ai-automation-2h67ix"

echo.
echo  LEDGER - setup
echo  ==============
echo.

where git >nul 2>nul || (
  echo  Git is not installed - it is what copies the project down.
  echo.
  echo  Get it from https://git-scm.com/downloads
  echo  Click through the installer with all the defaults; they are fine.
  echo  Then run this file again.
  echo.
  pause & exit /b 1
)
where python >nul 2>nul || (
  echo  Python is not installed.
  echo.
  echo  Get it from https://python.org/downloads
  echo  On the installer's FIRST screen tick "Add python.exe to PATH".
  echo  That tickbox is easy to miss and nothing works without it.
  echo  Then run this file again.
  echo.
  pause & exit /b 1
)

if exist "%REPO%\.git" (
  echo  Project already at %REPO% - updating it.
  pushd "%REPO%"
  git fetch origin || echo  (fetch failed, carrying on with what is here)
  git checkout "%BRANCH%" 2>nul || git checkout -b "%BRANCH%" "origin/%BRANCH%"
  git pull origin "%BRANCH%"
  popd
) else (
  echo  Copying the project to %REPO% ...
  echo.
  echo  A GitHub sign-in window may appear. That is normal - it is your
  echo  own account, and it is how git proves you may read the project.
  echo.
  git clone --branch "%BRANCH%" https://github.com/jsab258/wc26-picks.git "%REPO%" || (
    echo.
    echo  That did not work. The usual cause is the sign-in being
    echo  cancelled or timing out. Run this file again and complete it.
    echo.
    echo  If it keeps failing, tell me what it printed and I will sort it.
    pause & exit /b 1
  )
)

if not exist "%REPO%\tools\mixamo-pick\GO.bat" (
  echo  The project copied but GO.bat is not where I expected.
  echo  Tell me and I will sort it.
  pause & exit /b 1
)

echo.
echo  ------------------------------------------------------------
echo   Project is at %REPO%
echo   Starting the Mixamo harvest now.
echo  ------------------------------------------------------------
echo.
pause
call "%REPO%\tools\mixamo-pick\GO.bat"
