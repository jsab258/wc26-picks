@echo off
REM LEDGER voice casting, step 1 of 2.
REM Double-click this. It installs what it needs, streams the candidate
REM voices, and opens a web page with players and the casting brief above
REM each character. Listen, then type your picks into picks.txt.
cd /d "%~dp0"
where python >nul 2>nul || (
  echo Python is not installed. Get it from https://python.org/downloads
  echo On the installer's first screen, tick "Add python.exe to PATH".
  pause
  exit /b 1
)
python ledger_voice_fetch.py --yes
if errorlevel 1 goto :failed

echo.
echo ---------------------------------------------------------------
echo A page should have opened. Listen, then write your picks into
echo    ledger-voices-out\picks.txt
echo and double-click "2 INSTALL.bat".
echo ---------------------------------------------------------------
pause
exit /b 0

:failed
REM  THIS USED TO PRINT "A page should have opened" WHATEVER HAPPENED.
REM  The first real run failed to reach any corpus and said it anyway,
REM  which is the same unconditional-success banner that claimed a push
REM  had happened under a rejected push an hour earlier.
echo.
echo ---------------------------------------------------------------
echo The fetch FAILED and no page was opened - the reason is above.
echo Nothing is broken on your machine; send me those lines.
echo ---------------------------------------------------------------
pause
exit /b 1
