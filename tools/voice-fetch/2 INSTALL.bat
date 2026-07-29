@echo off
REM LEDGER voice casting, step 2 of 2.
REM Run this AFTER you have written your picks into
REM ledger-voices-out\picks.txt. It builds the final reference clips.
cd /d "%~dp0"
python ledger_voice_fetch.py --install --yes
echo.
echo Done. Tell Claude it is installed and the bark bank can be generated.
pause
