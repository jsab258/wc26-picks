@echo off
REM  PUT THE VOICES INTO A DOWNLOADED BUILD.
REM
REM  Drag the unzipped LEDGER build folder onto this file, or run it and
REM  paste the path when it asks. It copies the three graphs from
REM  game-out into the build so characters speak; everything else the
REM  game needs is already in there.
setlocal
cd /d "%~dp0..\.."

set "BUILD=%~1"
if "%BUILD%"=="" set /p BUILD=Path to the unzipped LEDGER folder:

python "tools\put-voices-in-build.py" "%BUILD%"
if errorlevel 1 (
  echo.
  echo Nothing was copied. The line above says why.
)
echo.
pause
