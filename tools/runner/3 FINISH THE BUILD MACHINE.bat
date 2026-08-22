@echo off
setlocal
title LEDGER - finish the build machine
REM ===================================================================
REM  The first build on this PC found the two tools the cloud machine
REM  had and this one does not. This installs them:
REM
REM    - PowerShell 7 ("pwsh") - the build's verdict step runs on it
REM    - Python, machine-wide - only if missing for the service account
REM
REM  RUN AS ADMINISTRATOR (right-click, "Run as administrator") - a
REM  machine-wide install needs it. One-time; a build is dispatched
REM  automatically when this finishes.
REM ===================================================================
if /i "%~1"=="--fromtemp" goto :begin
copy /y "%~f0" "%TEMP%\ledger-finish.bat" >nul
"%TEMP%\ledger-finish.bat" --fromtemp
exit /b %errorlevel%
:begin

net session >nul 2>&1
if errorlevel 1 (
  echo  Needs administrator rights - right-click, "Run as administrator".
  pause & exit /b 1
)

set "REPO=%USERPROFILE%\wc26-picks"
set "BRANCH=claude/game-dev-ai-automation-2h67ix"

echo.
echo  LEDGER - finish the build machine
echo  =================================
echo.

where pwsh >nul 2>&1
if errorlevel 1 (
  echo  ---- installing PowerShell 7 (a few minutes) -----------------------
  winget install --id Microsoft.PowerShell -e --scope machine --accept-source-agreements --accept-package-agreements
  if errorlevel 1 goto :pwshfail
) else (
  echo  PowerShell 7 is already here.
)

where py >nul 2>&1
if errorlevel 1 (
  where python >nul 2>&1
  if errorlevel 1 (
    echo  ---- installing Python machine-wide --------------------------------
    winget install --id Python.Python.3.12 -e --scope machine --accept-source-agreements --accept-package-agreements
  ) else (
    echo  Python is here for this user; the build shims the rest.
  )
) else (
  echo  Python's launcher is already here.
)

echo.
echo  ---- restarting the runner service so it sees the new tools --------
for /f "tokens=1" %%s in ('sc query state^= all ^| findstr /i "actions.runner"') do set SVCLINE=1
powershell -NoProfile -Command "Get-Service 'actions.runner.*' | Restart-Service" 2>nul

echo.
echo  ---- telling Claude to dispatch a fresh build ----------------------
if exist "%REPO%\.git" (
  pushd "%REPO%"
  git pull origin "%BRANCH%" >nul 2>&1
  > tools\runner\DEPS.txt echo pwsh and python present on %COMPUTERNAME% at %DATE% %TIME%
  git add tools\runner\DEPS.txt >nul 2>&1
  git commit -m "Build machine finished: pwsh and python in place" >nul 2>&1
  git push origin HEAD:"%BRANCH%" >nul 2>&1 && echo   Sent - a build heads this way shortly.
  popd
) else (
  echo   Tell Claude "deps installed" in the chat.
)

echo.
echo  DONE.
echo.
pause
exit /b 0

:pwshfail
echo.
echo  The PowerShell 7 install FAILED - the reason is above. If winget
echo  is missing on this PC, install "App Installer" from the Microsoft
echo  Store once and run this again.
echo.
pause & exit /b 1
