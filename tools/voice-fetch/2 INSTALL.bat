@echo off
REM LEDGER voice casting, step 2 of 2.
REM Run this AFTER you have written your picks into
REM ledger-voices-out\picks.txt. It builds the final reference clips and
REM pushes them, which the first version did not - it copied the voices
REM into the project and left them sitting on this machine, the same gap
REM that stranded the Mixamo clips.
cd /d "%~dp0"
python ledger_voice_fetch.py --install --yes
if errorlevel 1 goto :failed

echo.
echo Installed. Pushing...
set "LEDGER_PUSH_PATH=ledger/Assets/Voices"
set "LEDGER_PUSH_MSG=Voice casting: reference clips from the listening pass"
call "%~dp0..\mixamo-pick\PUSH.bat"
set "LEDGER_PUSH_PATH="
set "LEDGER_PUSH_MSG="
exit /b %errorlevel%

:failed
echo.
echo The install failed - the reason is above. Nothing was pushed.
pause & exit /b 1
