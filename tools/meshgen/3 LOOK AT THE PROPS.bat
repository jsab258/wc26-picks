@echo off
setlocal enabledelayedexpansion

title LEDGER - look at the props
color 07

REM ===================================================================
REM  ONE CLICK. Double-click and walk away. Nothing is asked of you and
REM  nothing is typed. Blender opens showing every prop the pipeline
REM  has made on this PC, side by side, each one labelled with its name
REM  and its measured size, with a 1.8 m figure standing beside them
REM  for scale.
REM
REM  WHY THIS FILE EXISTS. Blender here is a portable extract, not an
REM  installation: the runner service account cannot install software
REM  (msiexec came back 1603 on rights), so a zip was unpacked instead.
REM  That means no Start menu entry, no desktop icon, no .glb file
REM  association and nothing under "apps" to find. Without this file
REM  you cannot open a mesh without being handed a path.
REM
REM  IT LOOKS, IT DOES NOT TOUCH. No mesh is modified, nothing is saved
REM  over anything, and not one byte is written into content\props.
REM  Everything it writes goes to  %USERPROFILE%\ledger-meshgen,  which
REM  is the same scratch folder the prop maker already uses.
REM
REM  IT DOES NOT RUN GIT, ON PURPOSE, and this paragraph is here so the
REM  next person does not add one. The meshes it shows are the ones on
REM  THIS PC; they are not stored in git, so pulling could not fetch
REM  them and would only risk two things a viewer has no business
REM  risking - a merge prompt sitting in this window waiting for an
REM  answer nobody is here to give, and this file being rewritten
REM  underneath cmd while cmd is still reading it line by line. If you
REM  ever do add a git command here, set GIT_EDITOR first;
REM  tools\lint-bat-editor.py fails the build for any .bat that does
REM  not, and it exists because exactly that hung Jafar's window once.
REM
REM  IN ORDER:
REM    1. Find Blender, by running the toolchain probe the prop maker
REM       already uses. There is no second copy of that search here.
REM    2. Count the props and PRINT WHAT IT FOUND, before any window
REM       opens. No props and no Blender are different answers and are
REM       said differently.
REM    3. Open Blender on the batch. Close the window when done.
REM
REM  NOTHING IS BOUGHT AND NO ACCOUNT IS USED.
REM
REM  THIS FILE HAS NEVER BEEN RUN WHERE IT WAS WRITTEN - there is no
REM  Windows, no PowerShell and no Blender there. Every decision it
REM  makes is one line of cmd reading a file some tested tool wrote;
REM  the finding, the measuring and the laying out are all in
REM  tools\meshgen\propview.py, which has a selftest.
REM ===================================================================

echo.
echo   LEDGER - look at the props
echo   ==========================
echo.

REM --- where is the repository? ---------------------------------------
set "REPO=%~dp0..\.."
for %%I in ("%REPO%") do set "REPO=%%~fI"
if not exist "%REPO%\CLAUDE.md" set "REPO=%USERPROFILE%\wc26-picks"
if not exist "%REPO%\CLAUDE.md" (
  echo   NOTE: could not find the LEDGER project folder.
  echo         Looked in "%~dp0..\.." and "%USERPROFILE%\wc26-picks".
  echo         Without it there is nothing to look at. Move this folder
  echo         back into the project and click again.
  goto :theend
)
set "PROPS=%REPO%\content\props"
set "WS=%USERPROFILE%\ledger-meshgen"
if not exist "%WS%" mkdir "%WS%" 2>nul
if not exist "%WS%" (
  echo   FAILED before starting: cannot create "%WS%".
  echo   Send that line back - it usually means the profile is
  echo   redirected or the disk is full.
  goto :theend
)
set "ANSWER=%WS%\blender-answer.txt"
set "TOOLS=%WS%\tools.json"
set "STATUS=%WS%\propview-status.txt"
set "REPORT=%WS%\propview-report.txt"
set "OPENED=%WS%\propview-opened.txt"

REM  LAST CLICK'S ANSWERS ARE DELETED BY NAME, and only these two, so a
REM  run that produces nothing cannot be read as this run's result. The
REM  glob that once deleted sixteen characters' worth of work is the
REM  reason this names its files instead of clearing a folder.
del /q "%ANSWER%" >nul 2>nul
del /q "%STATUS%" >nul 2>nul
del /q "%OPENED%" >nul 2>nul

echo   project : %REPO%
echo   props   : %PROPS%
echo.

REM --- 1. find Blender -------------------------------------------------
echo   [1/3] Looking for Blender. This also refreshes the toolchain
echo         report, so give it up to half a minute.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0where-blender.ps1" -Answer "%ANSWER%" -ToolsOut "%TOOLS%"
if not exist "%ANSWER%" (
  echo.
  echo   COULD NOT LOOK FOR BLENDER AT ALL. PowerShell did not run, or
  echo   it wrote nothing to
  echo     %ANSWER%
  echo   That is NOT the same as Blender being missing - nothing looked.
  echo   Send this window back.
  goto :theend
)
set "BL="
set /p BL=<"%ANSWER%"
if not defined BL (
  echo.
  echo   BLENDER IS NOT ON THIS PC, and here is exactly where it looked:
  echo.
  type "%ANSWER%"
  echo.
  echo   FIX: Blender is free from blender.org and needs no account. On
  echo   this machine it is normally unpacked by the project rather than
  echo   installed, so if it was there before, the folder has moved or
  echo   been cleared. Nothing was opened.
  goto :theend
)
if not exist "%BL%" (
  echo.
  echo   The toolchain report names a Blender that is no longer there:
  echo     %BL%
  echo   Nothing was opened. If Blender was moved, click this again -
  echo   the search runs fresh every time.
  goto :theend
)
echo         found: %BL%
echo.

REM --- 2. what is there, before anything opens -------------------------
REM  THE COUNT COMES FROM BLENDER'S OWN PYTHON, headless, so there is no
REM  second tool to find and no second copy of the rule about what a
REM  prop is. It writes a STATUS FILE and this reads that, never the
REM  exit code: Blender exits 0 after a script that raised.
echo   [2/3] Counting the props...
"%BL%" --background --factory-startup --python "%~dp0propview.py" -- --props "%PROPS%" --status "%STATUS%" --report "%REPORT%"
if not exist "%STATUS%" (
  echo.
  echo   THE COUNT PRODUCED NOTHING. Blender ran but wrote no answer to
  echo     %STATUS%
  echo   so this is a fault in the viewer, not a fact about the props.
  echo   Nothing was opened. Send back the lines above.
  goto :theend
)
set "STAT="
set /p STAT=<"%STATUS%"
for /f "tokens=1,2" %%A in ("!STAT!") do (
  set "STATE=%%A"
  set "COUNT=%%B"
)
if "!STATE!"=="NODIR" (
  echo.
  echo   THERE IS NO PROPS FOLDER ON THIS PC at
  echo     %PROPS%
  echo   so this is probably not the project folder rather than an empty
  echo   batch. Nothing was opened.
  goto :theend
)
if "!STATE!"=="NOPROPS" (
  echo.
  echo   NO PROPS HAVE BEEN MADE ON THIS PC YET. The folder is there and
  echo   holds no meshes. The meshes are not stored in the project, so
  echo   they have to be made here.
  echo.
  echo   FIX, one click: double-click  1 MAKE THE PROPS.bat  in this
  echo   same folder and walk away. It skips anything already done.
  echo   Nothing was opened.
  goto :theend
)
if not "!STATE!"=="OK" (
  echo.
  echo   The count wrote something this file does not understand:
  echo     !STAT!
  echo   Nothing was opened. Send back this window.
  goto :theend
)
echo.
echo         !COUNT! prop(s) to look at. The list above is the order they
echo         are laid out in, left to right, front row first.
echo.

REM --- 3. open it ------------------------------------------------------
echo   [3/3] Opening Blender. Close its window when you are done;
echo         nothing will be saved and nothing will be asked.
echo.
"%BL%" --factory-startup --python "%~dp0blender\view_props.py" -- --props "%PROPS%" --status "%OPENED%"

REM  WHAT WAS ACTUALLY ON THE SCREEN, in words, in this window. An empty
REM  Blender and a Blender showing the batch look identical from out here,
REM  and the empty one reads as "the props are broken" when it usually
REM  means the viewer failed. The window is the only channel he reads, so
REM  the three outcomes get three different paragraphs. The marker is
REM  written in a finally, so a viewer that crashed still leaves one.
set "OPENSTAT="
if exist "%OPENED%" set /p OPENSTAT=<"%OPENED%"
set "OPENSTATE="
set "OPENCOUNT="
for /f "tokens=1,2" %%A in ("!OPENSTAT!") do (
  set "OPENSTATE=%%A"
  set "OPENCOUNT=%%B"
)
echo.
echo   ============================================================
if "!OPENSTATE!"=="PLACED" (
  echo   Closed. !OPENCOUNT! prop(s) were on the screen, and nothing was
  echo   changed or saved.
  echo   The list of what you just looked at, in order, is in
  echo     %REPORT%
  echo   If one of them is wrong, say its NUMBER from that list.
) else if "!OPENSTATE!"=="NOTHING" (
  echo   BLENDER OPENED AND LOADED NOTHING. !COUNT! prop file(s) were
  echo   found on this PC, so this is a fault in the VIEWER, not a fact
  echo   about the props - they are still there and still fine.
  echo   The reason is in the lines above this box, and Blender said it
  echo   on its own screen too.
  echo   SEND BACK: this window. Nothing was changed or saved.
) else (
  echo   BLENDER CLOSED WITHOUT SAYING WHAT IT SHOWED. No marker at
  echo     %OPENED%
  echo   That usually means Blender itself failed to start or was killed
  echo   before the script ran, NOT that the props are missing - the
  echo   count above found !COUNT! of them.
  echo   SEND BACK: this window. Nothing was changed or saved.
)
echo   ============================================================

:theend
echo.
pause
endlocal
