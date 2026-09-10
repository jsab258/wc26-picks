@echo off
setlocal EnableExtensions EnableDelayedExpansion
REM ===================================================================
REM  MIGRATE TO LEDGER
REM
REM  Copies this project into its own repository at github.com/jsab258/ledger,
REM  exactly as it is. Nothing is rewritten, so EVERY COMMIT KEEPS THE SAME
REM  IDENTIFIER and every commit reference written in a decision record still
REM  resolves in the new repository.
REM
REM  Ruled by Jafar 2026-09-10: no Large File Storage and no data pack. An
REM  earlier version of this script moved large files into Large File Storage
REM  as it went; that rewrote history and changed every identifier, which is
REM  the thing this version deliberately does not do.
REM
REM  FOUR BRANCHES GO ACROSS, and one is deliberately left behind:
REM    main            this branch, renamed, and it keeps its identifiers
REM    art/atlas-01    the town atlas; the sheet compositor reads it directly
REM    pc-inbox        the message channel to and from this PC
REM    pc-results      the results side of that channel
REM  The bitcoin branch is NOT carried, per the ruling.
REM
REM  IT DOES NOT TOUCH THE OLD REPOSITORY. Everything happens in a new folder
REM  beside this one. If anything goes wrong, delete that folder and nothing
REM  has been lost.
REM
REM  THIS SCRIPT HAS NEVER BEEN RUN. The first run on this PC is its first run
REM  anywhere, which is why every step checks what it actually did instead of
REM  trusting that it worked.
REM
REM  Everything it prints also goes into migrate-to-ledger-log.txt beside it.
REM ===================================================================

set "SRC=https://github.com/jsab258/wc26-picks.git"
set "DST=https://github.com/jsab258/ledger.git"
set "WORK=%~dp0..\ledger-migrate"
set "MAINSRC=claude/game-dev-ai-automation-2h67ix"
set "LOG=%~dp0migrate-to-ledger-log.txt"
set /a MATCH=0
set /a CHECKED=0

echo ================================================== > "%LOG%"
echo MIGRATE TO LEDGER, started %DATE% %TIME% >> "%LOG%"
echo ================================================== >> "%LOG%"

echo.
echo   MIGRATE TO LEDGER
echo   -----------------
echo   From: %SRC%
echo   To:   %DST%
echo   Work folder: %WORK%
echo.
echo   History is copied unchanged, so every commit keeps the same
echo   identifier. Nothing in this folder is changed.
echo.

REM ---------- 1. Preflight ----------
echo [1/6] Checking what is installed and what already exists.
git --version >nul 2>&1
if errorlevel 1 goto NOGIT
for /f "delims=" %%v in ('git --version 2^>^&1') do echo       %%v
for /f "delims=" %%v in ('git --version 2^>^&1') do echo       %%v >> "%LOG%"

if exist "%WORK%" goto WORKEXISTS

echo       Checking the destination is reachable, BEFORE the long copy, so a
echo       repository that does not exist yet costs seconds and not an hour.
git ls-remote "%DST%" >nul 2>&1
if errorlevel 1 goto NODEST
echo       destination reachable.
echo       destination reachable >> "%LOG%"

REM ---------- 2. Copy ----------
echo.
echo [2/6] Copying the repository. About 2.6 GB. This takes a while.
git clone "%SRC%" "%WORK%" >> "%LOG%" 2>&1
if errorlevel 1 goto CLONEFAIL
cd /d "%WORK%"
if errorlevel 1 goto CLONEFAIL
echo       copied.

REM ---------- 3. The four branches ----------
echo.
echo [3/6] Setting up the four branches that other code actually reads.
git checkout -B main "origin/%MAINSRC%" >> "%LOG%" 2>&1
if errorlevel 1 goto BRANCHFAIL
call :KEEP art/atlas-01
call :KEEP pc-inbox
call :KEEP pc-results
echo       four branches ready. The bitcoin branch is not among them.

REM ---------- 4. Point at the new home ----------
echo.
echo [4/6] Adding the new home as a second remote. The old one stays
echo       connected and untouched.
git remote add ledger "%DST%" >> "%LOG%" 2>&1
if errorlevel 1 goto REMOTEFAIL

REM ---------- 5. Push ----------
echo.
echo [5/6] Sending the four branches.
echo       Note: eight files here are over 50 MB, which GitHub warns about but
echo       accepts. Nothing is over the 100 MB limit that it refuses, the
echo       largest being about 83 MB, so this should go through.
git push -u ledger main >> "%LOG%" 2>&1
if errorlevel 1 goto PUSHFAIL
git push ledger art/atlas-01 pc-inbox pc-results >> "%LOG%" 2>&1
if errorlevel 1 goto PUSHBRANCHFAIL
echo       sent.

REM ---------- 6. Prove the identifiers are identical ----------
REM  This is the check that matters. Counting branches only proves something
REM  arrived; comparing identifiers proves THE SAME THING arrived. Anything
REM  that rewrote history on the way would show up here as a mismatch.
echo.
echo [6/6] Comparing each branch's identifier here against the far end.
call :CHECKSHA main
call :CHECKSHA art/atlas-01
call :CHECKSHA pc-inbox
call :CHECKSHA pc-results
echo.
echo       identical: !MATCH! of !CHECKED! branch(es) compared
echo       identical=!MATCH!/!CHECKED! >> "%LOG%"
if !CHECKED! LSS 4 goto NOTALLCHECKED
if !MATCH! LSS 4 goto MISMATCHED

echo.
echo   ==================================================
echo   DONE. All four branches are at the new home and
echo   every one has the same identifier it has here, so
echo   nothing was rewritten on the way.
echo.
echo   TWO THINGS ARE STILL YOURS TO DO ON THE WEBSITE:
echo     1. Set the default branch to main.
echo     2. Give the Claude GitHub App access to the new
echo        repository, or no session can push to it.
echo.
echo   AND ONE MACHINE: the Windows runner still points at
echo   the old repository. Until it is re-registered, the
echo   studio cannot see its own builds.
echo.
echo   THE OLD REPOSITORY IS UNTOUCHED AND STILL WORKS.
echo   Do not stop using it until a full run has gone
echo   through on the new one.
echo   ==================================================
echo   DONE. identical=!MATCH!/!CHECKED! >> "%LOG%"
goto END

REM ---------- subroutines ----------
:KEEP
git branch --track %1 "origin/%1" >> "%LOG%" 2>&1
if errorlevel 1 echo       WARNING: could not set up %1, it may not exist upstream
if errorlevel 1 echo       WARNING could not set up %1 >> "%LOG%"
goto :eof

:CHECKSHA
set "LOCALSHA="
set "FARSHA="
for /f "delims=" %%a in ('git rev-parse %1 2^>nul') do set "LOCALSHA=%%a"
for /f "tokens=1" %%a in ('git ls-remote ledger refs/heads/%1 2^>nul') do set "FARSHA=%%a"
if "!LOCALSHA!"=="" goto CHECKSHA_NOLOCAL
if "!FARSHA!"=="" goto CHECKSHA_NOFAR
set /a CHECKED+=1
if /i "!LOCALSHA!"=="!FARSHA!" goto CHECKSHA_OK
echo       %1: DIFFERENT. here !LOCALSHA:~0,12! but there !FARSHA:~0,12!
echo       %1 MISMATCH here=!LOCALSHA! there=!FARSHA! >> "%LOG%"
goto :eof
:CHECKSHA_OK
set /a MATCH+=1
echo       %1: identical (!LOCALSHA:~0,12!)
echo       %1 identical !LOCALSHA! >> "%LOG%"
goto :eof
:CHECKSHA_NOLOCAL
echo       %1: nothing measured, no such branch here
echo       %1 nothing measured, absent locally >> "%LOG%"
goto :eof
:CHECKSHA_NOFAR
set /a CHECKED+=1
echo       %1: NOT AT THE FAR END AT ALL
echo       %1 absent at destination >> "%LOG%"
goto :eof

REM ---------- refusals ----------
:NOGIT
echo   STOPPED: Git is not installed, or not on the path.
echo   STOPPED no git >> "%LOG%"
goto END
:WORKEXISTS
echo   STOPPED: the work folder already exists:
echo     %WORK%
echo   That is either a run in progress or a finished one. Nothing is deleted
echo   automatically. Move it aside or delete it yourself, then run this again.
echo   STOPPED work folder exists >> "%LOG%"
goto END
:NODEST
echo   STOPPED: cannot reach %DST%
echo   Either it does not exist yet, or this PC cannot sign in to it. Create
echo   the empty repository on GitHub first, then run this again.
echo   STOPPED destination unreachable >> "%LOG%"
goto END
:CLONEFAIL
echo   STOPPED: the copy failed. See the log.
echo   STOPPED clone failed >> "%LOG%"
goto END
:BRANCHFAIL
echo   STOPPED: could not set up the main branch. See the log.
echo   STOPPED branch setup failed >> "%LOG%"
goto END
:REMOTEFAIL
echo   STOPPED: could not add the new home as a remote. See the log.
echo   STOPPED remote add failed >> "%LOG%"
goto END
:PUSHFAIL
echo   STOPPED: sending main failed.
echo   The likeliest causes are that this PC cannot write to the new
echo   repository yet, or that the connection dropped partway through a large
echo   send. Nothing is lost. The old repository is untouched and the work
echo   folder can be pushed again once the cause is fixed.
echo   STOPPED push main failed >> "%LOG%"
goto END
:PUSHBRANCHFAIL
echo   PARTIAL: main arrived but at least one of the other three branches did
echo   not. The atlas and the message channel live on those, so this is not
echo   finished. See the log.
echo   PARTIAL other branches failed >> "%LOG%"
goto END
:NOTALLCHECKED
echo   PARTIAL: only !CHECKED! of the 4 branches could be compared at all.
echo   PARTIAL checked=!CHECKED! >> "%LOG%"
goto END
:MISMATCHED
echo   STOPPED: !MATCH! of !CHECKED! branches match. An identifier that differs
echo   means something rewrote history on the way, which is exactly what this
echo   version is meant not to do. Do not start using the new repository. See
echo   the log.
echo   STOPPED mismatched identifiers >> "%LOG%"
goto END

:END
echo.
echo   Log written to: %LOG%
echo.
pause
endlocal
