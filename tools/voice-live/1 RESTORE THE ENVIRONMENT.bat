@echo off
setlocal
title LEDGER - restore the environment
REM ===================================================================
REM  RUN THIS IF THE WATCHER SAYS THE PYTHON ENVIRONMENT IS MISSING.
REM
REM  What happened: an old commit on this machine had the whole virtual
REM  environment committed into git by accident. Matching the branch -
REM  which does not have it - therefore DELETED it, all hundred thousand
REM  files. My backup step saved the launcher and not the packages, which
REM  is a backup that protects the cheap half.
REM
REM  It is not gone. Git still has every one of those files in its object
REM  store, because they were committed. This takes them back out of the
REM  commit that had them and then UNTRACKS them, so the same thing can
REM  never happen twice: an untracked folder is not touched by matching
REM  the branch, and the project now ignores this path anyway.
REM
REM  Then it checks the environment actually works by importing the three
REM  packages every job needs. A folder full of files is not an
REM  environment, and finding that out later would cost another round of
REM  this.
REM ===================================================================

if /i "%~1"=="--fromtemp" goto :begin
copy /y "%~f0" "%TEMP%\ledger-restore.bat" >nul
"%TEMP%\ledger-restore.bat" --fromtemp
exit /b %errorlevel%
:begin

set "REPO=%USERPROFILE%\wc26-picks"
set "ENVPATH=tools/voice-live/env-export"
set "ENVDIR=%REPO%\tools\voice-live\env-export"

echo.
echo  LEDGER - restore the environment
echo  ================================
echo.
if not exist "%REPO%\.git" goto :norepo
cd /d "%REPO%"

if exist "%ENVDIR%\Scripts\python.exe" goto :alreadythere

REM  ORIG_HEAD is where this machine was before the branch was matched -
REM  git sets it on every reset, precisely so the previous state stays
REM  reachable. HEAD@{1} is the same idea one step further back, for the
REM  case where something else moved since.
echo  Looking for the environment in git's history...
call :try ORIG_HEAD
if exist "%ENVDIR%\Scripts\python.exe" goto :untrack
call :try "HEAD@{1}"
if exist "%ENVDIR%\Scripts\python.exe" goto :untrack
call :try "HEAD@{2}"
if exist "%ENVDIR%\Scripts\python.exe" goto :untrack
goto :notfound

:try
echo    trying %~1
git --no-pager checkout %1 -- "%ENVPATH%" >nul 2>&1
exit /b 0

:untrack
echo  Found it. Taking it back out of git's control...
REM  --cached leaves the files on disk and removes them from the index.
REM  The project ignores this path now, so it stays out for good.
git --no-pager rm -r --cached --quiet "%ENVPATH%" >nul 2>&1
git --no-pager reset --quiet -- "%ENVPATH%" >nul 2>&1

echo  Checking it actually runs...
"%ENVDIR%\Scripts\python.exe" -c "import torch, onnxruntime, chatterbox; print('  torch', torch.__version__, '/ onnxruntime', onnxruntime.__version__)"
if errorlevel 1 goto :broken

echo.
echo  DONE - the environment is back and it works.
echo.
echo  Start "8 START THE WATCHER.bat" and leave it open.
echo.
pause
exit /b 0

:alreadythere
echo  The environment is already here. Checking it runs...
"%ENVDIR%\Scripts\python.exe" -c "import torch, onnxruntime, chatterbox; print('  torch', torch.__version__, '/ onnxruntime', onnxruntime.__version__)"
if errorlevel 1 goto :broken
echo.
echo  Nothing to do - start "8 START THE WATCHER.bat".
echo.
pause
exit /b 0

:notfound
echo.
echo  Not in git's history here, so it has to be rebuilt from scratch.
echo  Run "2 TRY THE EXPORT.bat" - it downloads and installs everything
echo  and takes a while, but it needs no attention.
echo.
pause
exit /b 1

:broken
echo.
echo  The files came back but the environment does not import cleanly -
echo  only part of it had ever been committed, so this is a half of one.
echo.
echo  Run "2 TRY THE EXPORT.bat" to rebuild it properly. It takes a
echo  while and needs no attention.
echo.
pause
exit /b 1

:norepo
echo  No project at %REPO%
echo.
pause & exit /b 1
