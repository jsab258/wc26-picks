@echo off
REM LEDGER — put the voices into a downloaded build, so characters speak.
REM
REM DOUBLE-CLICK IT, or drop the unzipped build folder onto it. With no
REM argument the tool goes and finds the build itself: it looks in
REM Downloads, Desktop and your home folder for a player folder with
REM LEDGER_Data beside the exe, prefers one that was compiled with the
REM speech runtime, and names what it picked and what it passed over.
REM
REM THE THINKING IS IN THE PYTHON, ON PURPOSE. A .bat that searched
REM directories would be a .bat nobody could test until it was wrong on
REM somebody else's machine — the same lesson the watcher's header
REM records about the PowerShell fetch step. This file stays three lines
REM and `put-voices-in-build.py --selftest` covers the rest, both ways.
cd /d "%~dp0..\.."
python "tools\put-voices-in-build.py" %1
if errorlevel 1 goto :failed

echo.
echo Done. Start the build and walk up to somebody.
pause & exit /b 0

:failed
echo.
echo That did not work - the reason is above. Nothing was changed.
pause & exit /b 1
