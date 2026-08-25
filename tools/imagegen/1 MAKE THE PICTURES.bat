@echo off
setlocal enabledelayedexpansion
title LEDGER - make the pictures
color 07

REM ===================================================================
REM  ONE CLICK. Double-click this and walk away. Nothing else is asked
REM  of you - no menu, no choice, no key to press until it is done.
REM
REM  WHAT IT DOES, in order:
REM    1. Looks at this PC (graphics card, VRAM, driver, CPU, RAM, disk)
REM       and writes what it found into the repository so we can read it.
REM    2. Downloads a self-contained image generator and a model into
REM       %USERPROFILE%\ledger-imagegen - OUTSIDE the repository, so it
REM       can never be committed and never touches your Unity project,
REM       your Python, or the speech setup. Nothing is installed system
REM       wide. Nothing goes in Program Files. No registry, no PATH.
REM    3. Generates the first batch of Meridian signage into the game's
REM       own StreamingAssets folder, with a manifest.
REM
REM  DOWNLOAD: about 7-10 GB, ONCE. It resumes if you interrupt it.
REM  Delete %USERPROFILE%\ledger-imagegen to undo everything.
REM
REM  NOTHING IS BOUGHT AND NO ACCOUNT IS USED. The model is Apache-2.0
REM  and needs no login. If any download ever asks for one, the script
REM  STOPS and says so - that is your decision, not ours.
REM ===================================================================

echo.
echo   LEDGER - make the pictures
echo   ==========================
echo.
echo   One click. This will:
echo     - look at this PC and write a report we can read
echo     - download a generator + model (about 7-10 GB, once, resumable)
echo       into "%USERPROFILE%\ledger-imagegen"  (outside the repo)
echo     - generate 12 Meridian shop signs, notices and wall textures
echo.
echo   Nothing is installed system-wide. Nothing is bought. No account.
echo   Leave it running - the first run takes a while on any machine.
echo.

REM --- where is the repository? ---------------------------------------
set "REPO=%~dp0..\.."
for %%I in ("%REPO%") do set "REPO=%%~fI"
if not exist "%REPO%\CLAUDE.md" set "REPO=%USERPROFILE%\wc26-picks"
if not exist "%REPO%\CLAUDE.md" (
  echo   NOTE: could not find the LEDGER repository.
  echo         Looked in "%~dp0..\.." and "%USERPROFILE%\wc26-picks".
  echo         The pictures and the machine report will be written next to
  echo         this .bat instead, and you will need to copy them across.
  set "REPO="
)
set "WS=%USERPROFILE%\ledger-imagegen"
if not exist "%WS%" mkdir "%WS%" 2>nul
if not exist "%WS%" (
  echo.
  echo   FAILED before starting: cannot create "%WS%".
  echo   Send that line back - it usually means the profile is redirected
  echo   or the disk is full.
  goto :theend
)
echo   repository : %REPO%
echo   workspace  : %WS%
echo.

REM --- step 1: what is this machine? -----------------------------------
echo   [1/3] Looking at this PC...
set "MACHINE=%WS%\machine.json"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0probe-machine.ps1" -Out "%MACHINE%" -Drive "%SystemDrive%"
if not exist "%MACHINE%" (
  echo         The probe produced nothing. Carrying on anyway - the next
  echo         step will say plainly that it is planning blind, which is
  echo         better than guessing you have an NVIDIA card.
)

REM --- step 2: a Python to run the driver ------------------------------
REM  Stdlib only, so ANY Python 3.8+ works and we install NOTHING into it.
REM  Your speech environment is tried first because it is definitely here
REM  and using it read-only cannot disturb it.
echo   [2/3] Finding a Python (nothing will be installed into it)...
set "PY="
call :trypy "%REPO%\tools\voice-live\env-export\Scripts\python.exe"
if not defined PY call :trypy "%WS%\python-embed\python.exe"
if not defined PY for /f "delims=" %%P in ('where python.exe 2^>nul') do call :trypy "%%P"
if not defined PY (
  py -3 -c "import sys" >nul 2>&1
  if not errorlevel 1 set "PY=py -3"
)
if not defined PY (
  echo         No Python found. Fetching a small standalone copy...
  call :getembed
  call :trypy "%WS%\python-embed\python.exe"
)
if not defined PY (
  echo.
  echo   FAILED: no Python 3.8+ on this machine and the standalone copy
  echo   could not be downloaded either.
  echo.
  echo   Fix, one minute: install Python from the Microsoft Store, or from
  echo   python.org, then double-click this file again. Nothing else needs
  echo   to change - this script installs no Python packages at all.
  goto :theend
)
echo         using: %PY%

REM --- step 3: fetch, then generate ------------------------------------
echo   [3/3] Setting up and generating. This is the long part.
echo.
%PY% "%~dp0imagegen.py" all --machine "%MACHINE%" --workspace "%WS%" --repo "%REPO%" --max-minutes 60
set "RC=%errorlevel%"

echo.
echo   ============================================================
if "%RC%"=="0" (
  echo   DONE. Pictures and manifest.json are in:
  if defined REPO (
    echo     %REPO%\ledger\Assets\StreamingAssets\Decals\generated
  ) else (
    echo     %WS%\generated
  )
  echo.
  echo   SEND BACK: game-design\agent-reports\machine-report.txt
  echo   and open a couple of the PNGs first - if any of them shows a real
  echo   company's name or a recognisable face, say so and it gets binned.
) else if "%RC%"=="2" (
  echo   STOPPED: not enough free disk. See the message above.
) else if "%RC%"=="3" (
  echo   STOPPED during setup - NOTHING was generated. The reason is
  echo   printed above, in full.
  echo   SEND BACK: the last 20 lines of this window, and
  echo   %WS%\machine-report.txt
) else if "%RC%"=="4" (
  echo   The setup worked but EVERY image failed. That is a real finding
  echo   and the log above says why for each one.
  echo   SEND BACK: %WS%\machine-report.txt and this window.
) else (
  echo   Stopped with code %RC%. Send back this window.
)
echo   ============================================================
goto :theend

REM --------------------------------------------------------------------
:trypy
if defined PY exit /b 0
if "%~1"=="" exit /b 0
if not exist "%~1" exit /b 0
"%~1" -c "import sys; sys.exit(0 if sys.version_info>=(3,8) else 1)" >nul 2>&1
if errorlevel 1 exit /b 0
REM  QUOTES GO IN THE VALUE. "C:\Program Files\Python\python.exe" is the
REM  single likeliest path on any Windows box and an unquoted %PY% would run
REM  "C:\Program" with an argument. The `py -3` launcher below must stay
REM  unquoted, so the quoting lives here rather than at the call site.
set PY="%~1"
exit /b 0

:getembed
REM  UNVERIFIED PATH, said plainly: python.org is unreachable from the
REM  machine this script was written on, so these URLs were not tested.
REM  Three are tried and each one's failure is printed.
for %%V in (3.12.10 3.13.7 3.11.9) do (
  if not exist "%WS%\python-embed\python.exe" (
    echo           trying python %%V ...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$u='https://www.python.org/ftp/python/%%V/python-%%V-embed-amd64.zip'; try{Invoke-WebRequest -Uri $u -OutFile '%WS%\py.zip' -UseBasicParsing; Expand-Archive -Path '%WS%\py.zip' -DestinationPath '%WS%\python-embed' -Force; Write-Host ('           got ' + $u)}catch{Write-Host ('           failed: ' + $_.Exception.Message)}"
  )
)
exit /b 0

:theend
echo.
pause
endlocal
