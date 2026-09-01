@echo off
REM  ONE CLICK, MAKES NOTHING. Reads this PC, writes the report into the
REM  project, prints what could run here, and stops. About a minute.
REM
REM  It sets one variable and calls the other .bat, so there is exactly
REM  ONE copy of the update, the probes, the Python search and the exit
REM  codes. The same shape as the picture maker's two files, for the same
REM  reason: a second implementation is a second thing to be wrong.
set "GIT_EDITOR=true"
set "GIT_MERGE_AUTOEDIT=no"
set "LEDGER_MESHGEN_PROBE_ONLY=1"
call "%~dp01 MAKE THE PROPS.bat"
