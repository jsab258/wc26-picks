@echo off
REM One click: run the LEDGER overnight loop. STOP file is the kill switch:
REM create production\STOP to stop between iterations, delete it to allow.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-night.ps1"
pause
