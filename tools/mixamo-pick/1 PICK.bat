@echo off
REM LEDGER - pick the needed clips out of a MixamoHarvester run.
REM Drag the harvest's "animations" folder onto this file, or just
REM double-click and type the path when asked.
cd /d "%~dp0"
where python >nul 2>nul || (
  echo Python is not installed. Get it from https://python.org/downloads
  echo On the installer's first screen, tick "Add python.exe to PATH".
  pause
  exit /b 1
)
set "HARVEST=%~1"
if "%HARVEST%"=="" set /p HARVEST=Path to the harvest animations folder: 
python pick_animations.py --harvest "%HARVEST%"
echo.
echo ---------------------------------------------------------------
echo Now commit and push ledger\Assets\Characters - the fbx files AND
echo _catalogue.txt and _picks.json. The catalogue is the part that
echo stops me guessing at clip names.
echo ---------------------------------------------------------------
pause
