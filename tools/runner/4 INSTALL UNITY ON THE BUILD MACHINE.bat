@echo off
setlocal
title LEDGER - install Unity on the build machine
REM ===================================================================
REM  The build got past every tool check and stopped at Unity itself:
REM  the build service cannot install programs (Windows will not show
REM  an admin prompt to a background service), so Unity Hub and the
REM  editor must be put here once, by a person with the mouse. This
REM  is that once. The same layout the cloud machines had preinstalled.
REM
REM  WHAT IT DOES: installs Unity Hub, then Unity editor 6000.0.58f1
REM  - THE BIG ONE-TIME DOWNLOAD, several GB, typically 10-30 minutes.
REM  Progress prints as it goes. Afterwards every build just uses it.
REM
REM  JUST DOUBLE-CLICK THIS FILE. It asks for administrator permission
REM  itself, and every window stays open and says what happened.
REM ===================================================================

net session >nul 2>&1
if not errorlevel 1 goto :main

if /i "%~1"=="--elevated" (
  echo.
  echo  Windows opened this window WITHOUT administrator rights.
  echo  Tell Claude "no admin" in the chat.
  echo.
  pause
  exit /b 1
)

echo.
echo  Asking Windows for administrator permission - a prompt should
echo  appear now. Click Yes.
echo.
powershell -NoProfile -Command "try { Start-Process cmd.exe -ArgumentList '/k','\"%~f0\" --elevated' -Verb RunAs -ErrorAction Stop } catch { exit 1 }"
if errorlevel 1 (
  echo  The permission prompt was refused or blocked.
) else (
  echo  If a new LEDGER window appeared, follow it - this one is done.
)
echo.
echo  If NO new window appeared, do it by hand:
echo    1. press the Windows key and type: cmd
echo    2. right-click "Command Prompt", choose "Run as administrator"
echo    3. paste this line into it and press Enter:
echo.
echo    "%~f0" --elevated
echo.
pause
exit /b 0

:main
set "REPO=%USERPROFILE%\wc26-picks"
set "BRANCH=claude/game-dev-ai-automation-2h67ix"
set "HUB=C:\Program Files\Unity Hub\Unity Hub.exe"
set "EDITOR=C:\Program Files\Unity\Hub\Editor\6000.0.58f1\Editor\Unity.exe"

echo.
echo  LEDGER - install Unity on the build machine
echo  ===========================================
echo.

if exist "%HUB%" (
  echo  Unity Hub is already installed.
  goto :editor
)
echo  ---- fetching Unity Hub - about 150 MB -----------------------------
curl.exe -L --fail --retry 2 --retry-delay 3 -o "%TEMP%\UnityHubSetup-x64.exe" "https://public-cdn.cloud.unity3d.com/hub/prod/UnityHubSetup-x64.exe"
if errorlevel 1 (
  echo.
  echo  The download FAILED - the reason is above. Is the internet up?
  pause
  exit /b 1
)
echo  ---- installing Unity Hub (silent, under a minute) -----------------
"%TEMP%\UnityHubSetup-x64.exe" /S
if not exist "%HUB%" (
  echo.
  echo  Unity Hub did not land - something on this PC is blocking its
  echo  installer. Tell Claude, and say which antivirus this PC runs.
  pause
  exit /b 1
)
echo  Unity Hub installed.

:editor
if exist "%EDITOR%" (
  echo  Unity 6000.0.58f1 is already installed.
  goto :acl
)
echo.
echo  ---- installing Unity editor 6000.0.58f1 ---------------------------
echo  THE BIG ONE: several GB. Typically 10-30 minutes. Progress below;
echo  the window may sit quietly between stages - that is normal.
echo.
"%HUB%" -- --headless install --version 6000.0.58f1 --changeset 44b8bf3a3225 --module windows-il2cpp --childModules
if not exist "%EDITOR%" (
  echo.
  echo  The editor did not land - the reason is in the lines above.
  echo  Tell Claude what the last few lines say.
  pause
  exit /b 1
)
echo.
echo  Unity editor installed.

:acl
REM The build service activates Unity's licence at build time and the
REM licence file lives under ProgramData\Unity - which the service
REM account cannot create. Granted once here, so the first licensed
REM build does not become the next silent failure.
if not exist "C:\ProgramData\Unity" mkdir "C:\ProgramData\Unity"
icacls "C:\ProgramData\Unity" /grant "NETWORK SERVICE:(OI)(CI)M" >nul 2>&1
echo  Licence folder prepared for the build service.

echo.
echo  ---- telling Claude to dispatch a fresh build ----------------------
if exist "%REPO%\.git" (
  pushd "%REPO%"
  > tools\runner\UNITY.txt echo Unity 6000.0.58f1 installed on %COMPUTERNAME% at %DATE% %TIME%
  git add tools\runner\UNITY.txt >nul 2>&1
  git commit -m "Unity installed on the build machine" >nul 2>&1
  git push origin HEAD:%BRANCH% >nul 2>&1 && (
    echo   Sent - a build heads this way shortly.
  ) || (
    echo   Could not push the signal - tell Claude "unity installed" in the chat.
  )
  popd
) else (
  echo   No project folder at %REPO% from this account.
  echo   Tell Claude "unity installed" in the chat.
)

echo.
echo  DONE. This window can be closed.
echo.
pause
exit /b 0
