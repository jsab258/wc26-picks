@echo off
setlocal enabledelayedexpansion
REM  GIT MUST NEVER OPEN AN EDITOR HERE. 26 Aug: a `git pull` that made a merge
REM  commit opened vim in Jafar's window, he closed it, and the half-finished
REM  merge blocked every pull afterwards - which read as "the pull is broken"
REM  rather than "something is waiting for you". `true` exits 0 immediately, so
REM  git takes the default message and carries on. tools/lint-bat-editor.py
REM  fails the build for any .bat that runs git without this.
set "GIT_EDITOR=true"
set "GIT_MERGE_AUTOEDIT=no"

title LEDGER - make the props
color 07

REM ===================================================================
REM  ONE CLICK. Double-click and walk away. Nothing is asked of you.
REM
REM  WHAT IT DOES, in order:
REM    1. Updates the project, then looks at this PC twice: the hardware
REM       (graphics card, VRAM, RAM, disk - the same probe the picture
REM       maker uses) and the toolchain (Blender, Python, CUDA, MSVC,
REM       git, bash).
REM    2. DECIDES WHETHER THE RUN CAN HAPPEN AT ALL, before making one
REM       file. If the batch needs something this PC has not got, it
REM       STOPS, names every missing piece with what would fix it, and
REM       writes the report into the project so we can read it. It does
REM       NOT half-install anything and it does not report success over
REM       a run that did nothing.
REM    3. Otherwise it grinds the batch: for each prop, clean it in
REM       Blender, build the LOD chain, measure every export, tag it
REM       with its licence, and write the manifest. Hours, unattended.
REM
REM  RESUMABLE. Anything already made and still measuring correctly is
REM  SKIPPED and said so. Stop it whenever you like and click again.
REM
REM  KILL SWITCH: create the file  production\STOP  in the project and
REM  it stops between items, keeping everything already made. Delete
REM  the file to allow the next run. Same switch as the night runner.
REM
REM  NOTHING IS BOUGHT AND NO ACCOUNT IS USED. Blender is free from
REM  blender.org. No paid service is called and none is authorised.
REM
REM  THIS FILE HAS NEVER BEEN RUN WHERE IT WAS WRITTEN - there is no
REM  Windows there. Everything it hands to Python is tested (meshgen.py
REM  --selftest); this file's own control flow is not, which is exactly
REM  why every DECISION lives in meshgen.py and not up here.
REM ===================================================================

set "PYARGS="
if defined LEDGER_MESHGEN_PROBE_ONLY set "PYARGS=probe"
if not defined LEDGER_MESHGEN_PROBE_ONLY set "PYARGS=run"
if defined LEDGER_MESHGEN_SPEC set "SPECARG=--spec"
if not defined LEDGER_MESHGEN_SPEC set "SPECARG="

echo.
echo   LEDGER - make the props
echo   =======================
echo.
if defined LEDGER_MESHGEN_PROBE_ONLY (
  echo   LOOK ONLY. This makes nothing. It reads this PC, writes the
  echo   report into the project, and tells you what could run here.
  echo   About one minute.
) else (
  echo   One click. This will:
  echo     - update the project and look at this PC
  echo     - STOP right there, having made nothing, if the batch cannot
  echo       run here - and say exactly what is missing
  echo     - otherwise clean, LOD, measure and licence-tag every prop in
  echo       the batch, skipping anything already done
)
echo.
echo   Kill switch: create  production\STOP  to stop between items.
echo.

REM --- where is the repository? ---------------------------------------
set "REPO=%~dp0..\.."
for %%I in ("%REPO%") do set "REPO=%%~fI"
if not exist "%REPO%\CLAUDE.md" set "REPO=%USERPROFILE%\wc26-picks"
if not exist "%REPO%\CLAUDE.md" (
  echo   NOTE: could not find the LEDGER repository.
  echo         Looked in "%~dp0..\.." and "%USERPROFILE%\wc26-picks".
  echo         Without it there is no batch to run and nowhere to write
  echo         the report. Fix the folder location and click again.
  goto :theend
)
set "WS=%USERPROFILE%\ledger-meshgen"
if not exist "%WS%" mkdir "%WS%" 2>nul
if not exist "%WS%" (
  echo   FAILED before starting: cannot create "%WS%".
  echo   Send that line back - it usually means the profile is
  echo   redirected or the disk is full.
  goto :theend
)
echo   repository : %REPO%
echo   workspace  : %WS%
echo.

REM --- update first ----------------------------------------------------
REM  A FAILED PULL IS NOT FATAL but it is SAID: "ran the old code" and
REM  "ran the new code" must not look identical in the only window
REM  anybody reads.
echo   [0/4] Updating the project...
for %%F in ("%~f0") do set "SELFWAS=%%~tF %%~zF"
pushd "%REPO%"
git pull origin claude/game-dev-ai-automation-2h67ix
if errorlevel 1 (
  echo         PULL FAILED - carrying on with the copy already on this PC.
  echo         If this run behaves like an older one, that is why.
)
popd
for %%F in ("%~f0") do set "SELFNOW=%%~tF %%~zF"
REM  THE BOOTSTRAP HOLE. cmd reads a .bat line by line AS IT RUNS, so a
REM  pull that rewrites this file mid-run leaves cmd reading from a byte
REM  offset into different text. If the pull changed this file, start the
REM  new one and stop. LEDGER_RELAUNCHED makes it strictly once.
if not "%SELFWAS%"=="%SELFNOW%" if not defined LEDGER_RELAUNCHED (
  echo         This file was updated by the pull. Starting the new one.
  set "LEDGER_RELAUNCHED=1"
  call "%~f0"
  goto :theend
)
echo.

REM --- step 1: the hardware, using the probe that already exists -------
echo   [1/4] Looking at the hardware...
set "MACHINE=%WS%\machine.json"
powershell -NoProfile -ExecutionPolicy Bypass -File "%REPO%\tools\imagegen\probe-machine.ps1" -Out "%MACHINE%" -Drive "%SystemDrive%"
if not exist "%MACHINE%" (
  echo         The hardware probe produced nothing. The decision step will
  echo         say NOT MEASURED rather than guess - "we could not look" is
  echo         not "there is nothing there".
)

REM --- step 2: the toolchain ------------------------------------------
echo   [2/4] Looking at the toolchain...
set "TOOLS=%WS%\tools.json"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0probe-tools.ps1" -Out "%TOOLS%"
if not exist "%TOOLS%" (
  echo         The toolchain probe produced nothing. Same rule: the next
  echo         step will say so rather than assume an empty machine.
)

REM --- step 3: a Python to run the driver ------------------------------
REM  Stdlib only, so ANY Python 3.8+ works and NOTHING is installed into
REM  it. Blender carries its own Python and is not used for this.
echo   [3/4] Finding a Python (nothing will be installed into it)...
set "PY="
call :trypy "%REPO%\tools\voice-live\env-export\Scripts\python.exe"
call :trypy "%USERPROFILE%\miniconda3\python.exe"
if not defined PY for /f "delims=" %%P in ('where python.exe 2^>nul') do call :trypy "%%P"
if not defined PY (
  py -3 -c "import sys" >nul 2>&1
  if not errorlevel 1 set "PY=py -3"
)
if not defined PY (
  echo.
  echo   FAILED: no Python 3.8+ on this machine. Nothing was made.
  echo   Fix, one minute: install Python from the Microsoft Store or
  echo   python.org, then double-click this file again. This script
  echo   installs no Python packages at all.
  goto :theend
)
echo         using: %PY%

REM --- step 4: decide, then work ---------------------------------------
REM  THE DECISION IS PYTHON'S, NOT THIS FILE'S. meshgen.py runs the gate
REM  before it makes anything and exits 5 if it refuses, so the rule is
REM  enforced in the one layer here that has tests.
echo   [4/4] Deciding, then working. This is the long part.
echo.
%PY% "%~dp0meshgen.py" %PYARGS% --machine "%MACHINE%" --tools "%TOOLS%" --repo "%REPO%" --workspace "%WS%" --max-minutes 480 %SPECARG% %LEDGER_MESHGEN_SPEC%
set "RC=%errorlevel%"

echo.
echo   ============================================================
if "%RC%"=="0" (
  echo   DONE. The manifest says how many were made, how many were
  echo   skipped as already done, how many failed and how many were not
  echo   attempted - out of how many are in the batch. Read that line;
  echo   "done" on its own is not a measurement.
  echo.
  echo   The meshes and manifest.json are in  content\props\  and the
  echo   report is in  production\mesh-reports\.
  echo.
  echo   NOTHING TO SEND if the lines above say SENT. If they say
  echo   SENDING BACK IS OFF or PUSH FAILED, they name the reason and
  echo   that is the only case where anything needs carrying by hand.
) else if "%RC%"=="5" (
  echo   STOPPED BEFORE MAKING ANYTHING - on purpose. This PC cannot run
  echo   the batch that was asked for. Every missing piece is listed
  echo   above with what would fix it, and the same list is in
  echo     production\mesh-reports\mesh-machine-report.txt
  echo.
  echo   That file is the answer we need. Nothing was downloaded and
  echo   nothing was installed.
) else if "%RC%"=="2" (
  echo   STOPPED: not enough free disk. The number is above.
) else if "%RC%"=="3" (
  echo   STOPPED during setup - NOTHING was made. The reason is above.
) else if "%RC%"=="4" (
  echo   The run happened and EVERY item failed. That is a real finding
  echo   and the log above says why for each one.
  echo   SEND BACK: the last 20 lines of this window.
) else if "%RC%"=="6" (
  echo   STOPPED by the kill switch (production\STOP). Everything made
  echo   so far is kept and counted in the manifest. Delete that file
  echo   to allow the next run.
) else if "%RC%"=="7" (
  echo   STOPPED BY THE LICENCE GATE. Something was produced that is not
  echo   properly tagged, or names a tool we may not ship. The lines
  echo   above name each one. This is a refusal on purpose: untagged
  echo   output is what the gate exists to catch.
) else if "%RC%"=="8" (
  echo   The batch file itself is unusable - the problems are listed
  echo   above, one sentence each. Nothing was made. This usually means
  echo   the project half-updated; run this again.
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
REM  QUOTES GO IN THE VALUE: "C:\Program Files\..." unquoted would run
REM  "C:\Program" with an argument. `py -3` above must stay unquoted, so
REM  the quoting lives here rather than at the call site.
set PY="%~1"
exit /b 0

:theend
echo.
pause
endlocal
