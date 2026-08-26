@echo off
setlocal enabledelayedexpansion
title LEDGER - make the pictures
color 07

REM ===================================================================
REM  ONE CLICK. Double-click this and walk away. Nothing else is asked
REM  of you - no menu, no choice, no command to paste, no file to move
REM  out of the way first, no key to press until it is done.
REM
REM  WHAT IT DOES, in order:
REM    1. Looks at this PC (graphics card, VRAM, driver, CPU, RAM, disk)
REM       and writes what it found into the repository so we can read it.
REM    2. DECIDES WHETHER THE RUN IS WORTH YOUR TIME - before downloading
REM       one byte. If no graphics card is found, or the look failed, it
REM       STOPS here: nothing downloaded, nothing generated, and it says
REM       what it found and which file to send back. It does NOT quietly
REM       fall back to the processor. That path measured 202 SECONDS PER
REM       PICTURE on 25 Aug and produced 2 of 12 in seven minutes - if
REM       you want it anyway it is the OTHER .bat, and that is one click
REM       too. This one never asks you to choose.
REM    3. Downloads a self-contained image generator and a model into
REM       %USERPROFILE%\ledger-imagegen - OUTSIDE the repository, so it
REM       can never be committed and never touches your Unity project,
REM       your Python, or the speech setup. Nothing is installed system
REM       wide. Nothing goes in Program Files. No registry, no PATH.
REM    4. Generates the Meridian signage into the game's own
REM       StreamingAssets folder, with a manifest - and SKIPS any picture
REM       that is already there and is not blank. Re-running is safe: it
REM       will not overwrite a good image, so nothing has to be copied
REM       aside by hand first. To have one made again, delete its .png.
REM
REM  DOWNLOAD: about 7-10 GB, ONCE. It resumes if you interrupt it.
REM  Delete %USERPROFILE%\ledger-imagegen to undo everything.
REM
REM  NOTHING IS BOUGHT AND NO ACCOUNT IS USED. The model is Apache-2.0
REM  and needs no login. If any download ever asks for one, the script
REM  STOPS and says so - that is your decision, not ours.
REM
REM  THIS FILE HAS NEVER BEEN RUN WHERE IT WAS WRITTEN - there is no
REM  Windows and no PowerShell there. Version 1 of it DID run on Jafar's
REM  PC. Everything it hands to Python is tested; the .bat's own control
REM  flow is not, which is exactly why the STOP decision lives in
REM  imagegen.py (83 selftest checks, both ways) and not up here.
REM ===================================================================

REM  THE DELIBERATE SLOW PATH, passed by "2 MAKE THE PICTURES (no
REM  graphics card).bat" as an environment variable rather than as an
REM  argument: cmd's argument quoting is the single most fragile thing in
REM  this file and a variable cannot be mangled by a space in a path.
set "PYARGS="
if defined LEDGER_FORCE_CPU set "PYARGS=--force-cpu"
if defined LEDGER_REDO set "PYARGS=%PYARGS% --redo"

echo.
echo   LEDGER - make the pictures
echo   ==========================
echo.
if defined LEDGER_FORCE_CPU (
  echo   SLOW PATH - you double-clicked the "no graphics card" one.
  echo   This will use the processor. It made 2 half-size pictures in
  echo   about seven minutes last time. That is expected, not a fault.
) else (
  echo   One click. This will:
  echo     - look at this PC and write a report we can read
  echo     - STOP right there, having downloaded nothing, if this PC has
  echo       no graphics card - and tell you what to send back
  echo     - otherwise download a generator + model ^(about 7-10 GB, once,
  echo       resumable^) into "%USERPROFILE%\ledger-imagegen"  ^(outside the repo^)
  echo     - generate 12 Meridian shop signs, notices and wall textures,
  echo       skipping any that are already made
)
echo.
echo   Nothing is installed system-wide. Nothing is bought. No account.
echo   Pictures you already have are never overwritten.
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
set "PROBE_RC=%errorlevel%"
REM  EXACTLY 10, NOT `if errorlevel 10`. That is a GREATER-OR-EQUAL test in
REM  cmd, and a powershell.exe that will not start at all sets 9009 - which
REM  would read as "this PC has no graphics card" on a PC nobody managed to
REM  look at. Any other code means UNKNOWN, and Python is left to say so from
REM  the file's side, where the wording is tested.
set "NOGPU="
if "%PROBE_RC%"=="10" set "NOGPU=1"
if defined LEDGER_FORCE_CPU set "NOGPU="
if not exist "%MACHINE%" (
  echo         The probe produced nothing. The next step will STOP rather
  echo         than guess you have an NVIDIA card - "we could not look" is
  echo         not "there is nothing there", and neither is worth 7 GB.
)
if defined NOGPU (
  echo.
  echo         NO DISPLAY ADAPTER FOUND. Nothing will be downloaded.
  echo         Writing the report now - the reason is printed below.
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
if not defined PY if not defined NOGPU (
  echo         No Python found. Fetching a small standalone copy...
  call :getembed
  call :trypy "%WS%\python-embed\python.exe"
)
if not defined PY if defined NOGPU (
  REM  NOT EVEN THE SMALL DOWNLOAD. This run was already going to stop; a
  REM  25 MB fetch to write a report about a run that will not happen is the
  REM  same fault as the 7 GB one, in miniature.
  echo.
  echo   ============================================================
  echo   STOPPED. This PC reports NO display adapter, and there is no
  echo   Python here to write the full report with. NOTHING was
  echo   downloaded and nothing was generated.
  echo.
  echo   SEND BACK: %MACHINE%
  echo   ^(that is the raw probe output - it says what was looked for^)
  echo.
  echo   If you want the processor run anyway, double-click
  echo     "2 MAKE THE PICTURES (no graphics card).bat"
  echo   ============================================================
  goto :theend
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

REM --- step 3: decide, then fetch, then generate -----------------------
REM  THE DECISION IS PYTHON'S, NOT THIS FILE'S. imagegen.py runs its gate
REM  before the first byte is downloaded and exits 5 if it stops, so the rule
REM  is enforced in the one layer here that has tests - this .bat's NOGPU flag
REM  above is only an optimisation that avoids fetching a Python for a run
REM  that is not going to happen.
if defined NOGPU (
  echo   [3/3] Writing the report. NOTHING will be downloaded.
) else (
  echo   [3/3] Setting up and generating. This is the long part.
)
echo.
%PY% "%~dp0imagegen.py" all --machine "%MACHINE%" --workspace "%WS%" --repo "%REPO%" --max-minutes 60 %PYARGS%
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
  echo   Anything already made was SKIPPED, not overwritten - the count is
  echo   in the summary just above. To have one made again, delete its
  echo   .png and double-click this file again.
  echo.
  echo   NOTHING TO SEND. This run pushed the pictures and its own report
  echo   to the project itself - the lines a few above say "SENT:" and how
  echo   many. If instead they say SENDING BACK IS OFF, or that a push
  echo   failed, they name the reason and what to do; that is the only case
  echo   where anything needs carrying by hand.
  echo.
  echo   ONE THING THAT IS STILL YOURS: open a couple of the PNGs. If any
  echo   shows a real company's name or a recognisable face, say so and it
  echo   gets binned.
) else if "%RC%"=="5" (
  echo   STOPPED BEFORE DOWNLOADING ANYTHING - on purpose. The reason is
  echo   printed above in full. Nothing was downloaded, nothing was
  echo   generated, and no time was spent on a run whose answer was
  echo   already known.
  echo.
  echo   SEND BACK: game-design\agent-reports\machine-report.txt
  echo   ^(or %WS%\machine-report.txt if the repo was not found^)
  echo.
  echo   If you want the processor run anyway - 2 half-size pictures in
  echo   about seven minutes - double-click
  echo     "2 MAKE THE PICTURES (no graphics card).bat"
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
