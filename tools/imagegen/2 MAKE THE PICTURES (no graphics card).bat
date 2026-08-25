@echo off
setlocal
title LEDGER - make the pictures on the processor (slow, on purpose)
color 07

REM ===================================================================
REM  THE SLOW PATH, ON PURPOSE. Double-click this ONLY if "1 MAKE THE
REM  PICTURES.bat" stopped and said this PC has no graphics card, and
REM  you want the pictures made by the processor anyway.
REM
REM  WHY IT IS A SEPARATE FILE. The one-click rule is that the normal
REM  path never asks you anything - so the normal path cannot offer a
REM  choice between fast and slow, and it cannot spend seven minutes of
REM  your afternoon on a decision you did not make. That choice lives
REM  here instead, in a file whose name is the warning.
REM
REM  WHAT IT COSTS, measured on 25 Aug 2026 and not guessed: 202 SECONDS
REM  PER PICTURE. The batch is capped at the FIRST 2 of 12, at half
REM  size, so about seven minutes of generating - plus the 6.7 GB
REM  download the first time, which is the same download either way and
REM  is not repeated. The cap is deliberate: two pictures prove the
REM  wiring works, twelve would take an hour and prove the same thing.
REM
REM  IT IS THE SAME SCRIPT. This sets one variable and calls the other
REM  .bat, so there is exactly one copy of the download, the licence
REM  checks, the blank check and the skip. A second implementation is
REM  how two files drift apart until one of them is wrong.
REM
REM  NEVER RUN WHERE IT WAS WRITTEN - no Windows, no PowerShell there.
REM ===================================================================

echo.
echo   LEDGER - make the pictures WITHOUT a graphics card
echo   ==================================================
echo.
echo   This is the slow path and you meant to click it.
echo     - the processor draws each picture in about 202 seconds
echo     - only the first 2 of 12 are made, at half size
echo     - so: roughly seven minutes, after the one-time download
echo.
echo   If you have not run "1 MAKE THE PICTURES.bat" yet, run that one
echo   first - it will use your graphics card if there is one, which is
echo   about a hundred times faster.
echo.

REM  HERE first, then the name. "%~dp01 MAKE THE PICTURES.bat" is the same
REM  string and is legal - cmd takes the digit after the modifiers as the
REM  parameter - but the file we want starts with a "1", so writing it that
REM  way puts two different meanings of the character next to each other in
REM  a file nobody here can run to check. The variable costs a line.
set "HERE=%~dp0"
set "LEDGER_FORCE_CPU=1"
call "%HERE%1 MAKE THE PICTURES.bat"
endlocal
