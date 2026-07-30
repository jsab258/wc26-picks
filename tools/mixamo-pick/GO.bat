@echo off
setlocal enabledelayedexpansion
title LEDGER - Mixamo harvest
cd /d "%~dp0"

REM ===================================================================
REM  LEDGER - one click. Paste a token when Notepad opens; walk away.
REM
REM  The harvest lands OUTSIDE the repository on purpose: about a
REM  gigabyte, and none of it belongs in git except the picks.
REM ===================================================================

set "HARVEST=%USERPROFILE%\ledger-mixamo"

echo.
echo  LEDGER - Mixamo harvest
echo  =======================
echo.

where python >nul 2>nul || (
  echo  Python is not installed.
  echo  Get it from https://python.org/downloads and on the installer's
  echo  FIRST screen tick "Add python.exe to PATH".
  pause & exit /b 1
)
where git >nul 2>nul || (
  echo  Git is not installed. Get it from https://git-scm.com/downloads
  pause & exit /b 1
)

REM ---- 0. FIND THE SCRIPTS -----------------------------------------
REM  Run from a copy in Downloads the first time, which left the two
REM  Python files behind and failed four steps later with a path error.
REM  So look next to me first, then in the usual places a clone lands,
REM  and say something useful if none of them has it.
set "SCRIPTS="
if exist "%~dp0choose_characters.py" set "SCRIPTS=%~dp0"
if not defined SCRIPTS for %%D in (
  "%USERPROFILE%\wc26-picks"
  "%USERPROFILE%\Documents\wc26-picks"
  "%USERPROFILE%\Documents\GitHub\wc26-picks"
  "%USERPROFILE%\source\repos\wc26-picks"
  "%USERPROFILE%\Desktop\wc26-picks"
  "C:\dev\wc26-picks"
) do (
  if not defined SCRIPTS if exist "%%~D\tools\mixamo-pick\choose_characters.py" (
    set "SCRIPTS=%%~D\tools\mixamo-pick\"
  )
)
if not defined SCRIPTS (
  echo  I cannot find choose_characters.py and pick_animations.py.
  echo.
  echo  This file needs its two siblings. You are running it from
  echo      %~dp0
  echo  which does not have them - most likely a copy saved on its own.
  echo.
  echo  Fix: find your wc26-picks clone and run
  echo      tools\mixamo-pick\GO.bat
  echo  from inside it. Everything is already there.
  echo.
  echo  No clone? Then:
  echo      git clone https://github.com/jsab258/wc26-picks "%USERPROFILE%\wc26-picks"
  echo      cd "%USERPROFILE%\wc26-picks"
  echo      git checkout claude/game-dev-ai-automation-2h67ix
  echo  and run tools\mixamo-pick\GO.bat from there.
  pause & exit /b 1
)
echo  Scripts: %SCRIPTS%
for %%R in ("%SCRIPTS%..\..") do set "REPO=%%~fR"
echo  Repo:    %REPO%

REM ---- 1. the harvester --------------------------------------------
if not exist "%HARVEST%" mkdir "%HARVEST%"
if not exist "%HARVEST%\MixamoHarvester" (
  echo  [1/6] Fetching the harvester...
  git clone --depth 1 https://github.com/paulpierre/MixamoHarvester.git "%HARVEST%\MixamoHarvester" || (
    echo  Clone failed. Are you online?
    pause & exit /b 1
  )
) else (
  echo  [1/6] Harvester already present, reusing it.
)
set "MH=%HARVEST%\MixamoHarvester"

if exist "%MH%\mixamo_token.txt" (
  for %%A in ("%MH%\mixamo_token.txt") do if %%~zA GTR 10 goto :havetoken
)
echo.
echo  ------------------------------------------------------------
echo   I need a Mixamo token. It lives in your browser, not in mine.
echo.
echo   1. A Mixamo tab is about to open. Log in if you are not.
echo   2. Press F12, click "Console".
echo   3. Paste this and press Enter (it is on your clipboard now):
echo.
echo        localStorage.getItem('access_token')
echo.
echo   4. Copy the string it prints, WITHOUT the quotes.
echo   5. Notepad will open. Paste, save, close it.
echo  ------------------------------------------------------------
echo.
echo localStorage.getItem('access_token')| clip
start https://www.mixamo.com/
pause
type nul > "%MH%\mixamo_token.txt"
start /wait notepad "%MH%\mixamo_token.txt"
for %%A in ("%MH%\mixamo_token.txt") do if %%~zA LSS 10 (
  echo  That token file looks empty. Run this again when you have one.
  pause & exit /b 1
)
:havetoken
echo  Token present.

REM ---- 2. environment ----------------------------------------------
echo  [2/6] Python environment...
if not exist "%MH%\env" python -m venv "%MH%\env"
set "PY=%MH%\env\Scripts\python.exe"
"%PY%" -m pip install --quiet --upgrade pip
"%PY%" -m pip install --quiet -r "%MH%\requirements.txt" || (
  echo  Dependency install failed - the error is above.
  pause & exit /b 1
)

REM ---- 3. be a quieter guest ---------------------------------------
REM  `Set-Content -NoNewline` does not exist on Windows PowerShell 5.1
REM  and the first version used it, so the patch failed, printed a red
REM  error, and the script sailed on with the default five threads.
REM  WriteAllText works everywhere - and the result is now CHECKED,
REM  because a silent patch failure is worse than a loud one.
REM  The count is READ, not hard-coded, because GO.bat is also what you
REM  re-run to resume a harvest - so hard-coding 2 here would silently
REM  undo FASTER.bat every single time.
set "THREADS=2"
if exist "%MH%\threads.txt" set /p THREADS=<"%MH%\threads.txt"
echo  [3/6] Setting %THREADS% threads...
powershell -NoProfile -Command ^
  "$p='%MH%\mixamo_harvester.py'; $t=[IO.File]::ReadAllText($p); $t=$t -replace 'MAX_THREADS\s*=\s*\d+','MAX_THREADS = %THREADS%'; [IO.File]::WriteAllText($p,$t)"
findstr /C:"MAX_THREADS = %THREADS%" "%MH%\mixamo_harvester.py" >nul
if errorlevel 1 (
  echo  Could not set the thread count, and I will not pretend otherwise.
  echo  Tell me and I will sort it.
  pause & exit /b 1
)
echo         ...confirmed.

REM ---- 4. pin the characters ---------------------------------------
echo  [4/6] Pinning the character list...
python "%SCRIPTS%choose_characters.py" --harvester "%MH%" || (
  echo.
  echo  Could not pin the characters - see the message above. Nothing was
  echo  downloaded. The commonest cause is an expired token; they only
  echo  last a few hours. Delete
  echo      %MH%\mixamo_token.txt
  echo  and run me again.
  pause & exit /b 1
)

REM ---- 5. the harvest ----------------------------------------------
echo.
echo  [5/6] Harvesting. This is the long part - a couple of hours, and
echo        it is resumable, so closing this window costs you nothing.
echo.
pushd "%MH%"
"%PY%" mixamo_harvester.py
popd

REM ---- 6. pick and push --------------------------------------------
echo.
echo  [6/6] Picking the clips the game needs...
python "%SCRIPTS%pick_animations.py" --harvest "%MH%\animations" --out "%REPO%\ledger\Assets\Characters" || (
  echo  The pick failed - see above.
  pause & exit /b 1
)

echo.
echo  Pushing...
pushd "%REPO%"
git add "ledger/Assets/Characters"
git commit -m "Mixamo drop: characters and animation clips"
if errorlevel 1 echo  Nothing new to commit.
REM  REBASE ONTO THE REMOTE BEFORE PUSHING. Two hours will have passed
REM  since the harvest started and I will almost certainly have pushed
REM  something in the meantime; a push from behind is rejected outright.
git pull --rebase origin claude/game-dev-ai-automation-2h67ix
if errorlevel 1 echo  Rebase hit a snag - the push below may fail. Send me the output.
git push origin HEAD:claude/game-dev-ai-automation-2h67ix
if errorlevel 1 echo  Push failed. The clips are safe on disk - send me the output.
popd

echo.
echo  ==================================================================
echo   Done. The clips are in ledger\Assets\Characters and pushed.
echo   The full harvest stays at %HARVEST% - delete it whenever.
echo  ==================================================================
pause
