@echo off
setlocal enabledelayedexpansion
title LEDGER - Mixamo harvest
cd /d "%~dp0"

REM ===================================================================
REM  LEDGER - one click. Paste a token when Notepad opens; walk away.
REM
REM  Everything the harvest needs is done here: clone, environment,
REM  thread limit, pinning the character list so it does not try to
REM  download all hundred bodies, the harvest itself, picking the ~30
REM  clips the game needs out of ~2,500, and pushing them.
REM
REM  The harvest lands OUTSIDE the repository on purpose. It is about a
REM  gigabyte and none of it belongs in git except the picks.
REM ===================================================================

set "HARVEST=%USERPROFILE%\ledger-mixamo"
set "REPO=%~dp0..\.."

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

REM ---- 1. the token ------------------------------------------------
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
echo  [3/6] Limiting to 2 threads...
powershell -NoProfile -Command ^
  "$p='%MH%\mixamo_harvester.py'; $t=Get-Content -Raw $p; $t=$t -replace 'MAX_THREADS\s*=\s*\d+','MAX_THREADS = 2'; Set-Content -NoNewline $p $t"

REM ---- 4. pin the characters ---------------------------------------
echo  [4/6] Pinning the character list...
python "%~dp0choose_characters.py" --harvester "%MH%" || (
  echo.
  echo  Could not pin the characters - see the message above. Nothing was
  echo  downloaded. The commonest cause is an expired token; they only
  echo  last a few hours. Delete "%MH%\mixamo_token.txt" and run me again.
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
python "%~dp0pick_animations.py" --harvest "%MH%\animations" || (
  echo  The pick failed - see above.
  pause & exit /b 1
)

echo.
echo  Pushing...
pushd "%REPO%"
git add "ledger/Assets/Characters"
git commit -m "Mixamo drop: characters and animation clips" || echo  (nothing new to commit)
git push origin HEAD:claude/game-dev-ai-automation-2h67ix || echo  (push failed - tell me and I will sort it)
popd

echo.
echo  ==================================================================
echo   Done. The clips are in ledger\Assets\Characters and pushed.
echo   The full ~1GB harvest stays at %HARVEST% - delete it whenever.
echo  ==================================================================
pause
