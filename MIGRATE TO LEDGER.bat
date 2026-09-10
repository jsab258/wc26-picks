@echo off
setlocal EnableExtensions EnableDelayedExpansion
REM ===================================================================
REM  MIGRATE TO LEDGER
REM
REM  Copies this project into its own repository at github.com/jsab258/ledger,
REM  moving every file over 2 MB into Git Large File Storage as it goes, and
REM  keeping the history rather than starting from a blank slate.
REM
REM  IT DOES NOT TOUCH THE OLD REPOSITORY. Everything happens in a new folder
REM  beside this one. If anything goes wrong, delete that folder and nothing
REM  has been lost.
REM
REM  THIS SCRIPT HAS NEVER BEEN RUN. Git Large File Storage is not installed
REM  in the container that wrote it, so the first run on this PC is its first
REM  run anywhere. That is why every step checks what it actually did instead
REM  of trusting that it worked, and why it stops at the first thing that
REM  looks wrong rather than carrying on.
REM
REM  Everything it prints also goes into migrate-to-ledger-log.txt beside it.
REM ===================================================================

set "SRC=https://github.com/jsab258/wc26-picks.git"
set "DST=https://github.com/jsab258/ledger.git"
set "WORK=%~dp0..\ledger-migrate"
set "MAINSRC=claude/game-dev-ai-automation-2h67ix"
set "LOG=%~dp0migrate-to-ledger-log.txt"

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
echo   Nothing in this folder is changed. Everything happens in the work
echo   folder above. The full log is migrate-to-ledger-log.txt.
echo.

REM ---------- 1. Preflight. Refuse early and say why. ----------
echo [1/8] Checking what is installed and what already exists.
git --version >nul 2>&1
if errorlevel 1 goto NOGIT
for /f "delims=" %%v in ('git --version 2^>^&1') do echo       %%v
for /f "delims=" %%v in ('git --version 2^>^&1') do echo       %%v >> "%LOG%"

git lfs version >nul 2>&1
if errorlevel 1 goto NOLFS
for /f "delims=" %%v in ('git lfs version 2^>^&1') do echo       %%v
for /f "delims=" %%v in ('git lfs version 2^>^&1') do echo       %%v >> "%LOG%"

REM The whole migration rests on one flag. Ask the installed Git Large File
REM Storage whether it has that flag rather than guessing from its version
REM number, because a version string is a claim and this is a check.
git lfs migrate import --help 2>&1 | findstr /C:"--above" >nul
if errorlevel 1 goto NOABOVE
echo       the --above flag is present, so files can be selected by SIZE
echo       the --above flag is present >> "%LOG%"

if exist "%WORK%" goto WORKEXISTS

REM Does the destination exist and can we reach it? A clear refusal now beats
REM a confusing failure after a twenty minute copy.
echo       Checking the destination is reachable.
git ls-remote "%DST%" >nul 2>&1
if errorlevel 1 goto NODEST
echo       destination reachable.
echo       destination reachable >> "%LOG%"

REM ---------- 2. Copy the whole repository ----------
echo.
echo [2/8] Copying the repository. This is about 2.6 GB and will take a while.
git clone "%SRC%" "%WORK%" >> "%LOG%" 2>&1
if errorlevel 1 goto CLONEFAIL
cd /d "%WORK%"
if errorlevel 1 goto CLONEFAIL
echo       copied.

REM ---------- 3. Keep the four branches that are load-bearing ----------
REM  main            the working branch, renamed
REM  art/atlas-01    the town atlas; the sheet compositor reads it directly
REM  pc-inbox        the message channel to and from this PC
REM  pc-results      the results side of that channel
REM  The bitcoin branch is deliberately NOT carried, per the ruling.
echo.
echo [3/8] Keeping the four branches that other code actually reads.
git checkout -B main "origin/%MAINSRC%" >> "%LOG%" 2>&1
if errorlevel 1 goto BRANCHFAIL
call :KEEP art/atlas-01
call :KEEP pc-inbox
call :KEEP pc-results

REM Drop the link to the old repository so the rewrite below cannot see, and
REM therefore cannot rewrite or push, anything else that lived there.
git remote remove origin >> "%LOG%" 2>&1
echo       four branches kept, old repository disconnected.

REM ---------- 4. Count what should end up in Large File Storage ----------
echo.
echo [4/8] Counting the files over 2 MB before the move, so the number after
echo       the move has something to be compared against.
set /a BIG=0
for /f "tokens=4" %%s in ('git ls-tree -r -l HEAD 2^>nul') do if %%s GTR 2097152 set /a BIG+=1
echo       files over 2 MB on main right now: !BIG!
echo       filesOver2MB_before=!BIG! >> "%LOG%"

REM ---------- 5. The move itself ----------
echo.
echo [5/8] Moving every file over 2 MB into Large File Storage, through the
echo       whole history, on all four branches. This is the slow step.
echo       Selection is by SIZE, not by file name, which is deliberate: 89
echo       files here have spaces in their names and name patterns get those
echo       wrong.
git lfs install --local >> "%LOG%" 2>&1
git lfs migrate import --everything --above=2MB >> "%LOG%" 2>&1
if errorlevel 1 goto MIGRATEFAIL
echo       moved.

REM ---------- 6. Check the move actually happened ----------
echo.
echo [6/8] Checking the move rather than assuming it.
set /a NOWLFS=0
for /f "delims=" %%f in ('git lfs ls-files 2^>nul') do set /a NOWLFS+=1
echo       files now in Large File Storage on main: !NOWLFS!
echo       filesInLFS_after=!NOWLFS! >> "%LOG%"
if !NOWLFS! LSS 1 goto NOTHINGMOVED
if !NOWLFS! LSS !BIG! goto FEWERMOVED
if not exist ".gitattributes" goto NOATTRS
echo       a .gitattributes file was written, which is what tells every future
echo       clone to keep doing this.

REM ---------- 7. Push ----------
echo.
echo [7/8] Sending it to the new home. The large files go first and this is
echo       the step most likely to stop, because Large File Storage has an
echo       included allowance and this is about 1.1 GB.
git remote add origin "%DST%" >> "%LOG%" 2>&1
git push -u origin main >> "%LOG%" 2>&1
if errorlevel 1 goto PUSHFAIL
git push origin art/atlas-01 pc-inbox pc-results >> "%LOG%" 2>&1
if errorlevel 1 goto PUSHBRANCHFAIL
echo       sent.

REM ---------- 8. Check the far end, not the exit code ----------
echo.
echo [8/8] Checking what actually arrived at the far end.
set /a REMOTEBRANCHES=0
for /f "delims=" %%r in ('git ls-remote --heads origin 2^>nul') do set /a REMOTEBRANCHES+=1
echo       branches now at the new home: !REMOTEBRANCHES! of 4 expected
echo       remoteBranches=!REMOTEBRANCHES!/4 >> "%LOG%"
if !REMOTEBRANCHES! LSS 4 goto PARTIAL

echo.
echo   ==================================================
echo   DONE. The new home has all four branches and the
echo   large files are in Large File Storage.
echo.
echo   Files moved into Large File Storage: !NOWLFS!
echo   Branches at the new home: !REMOTEBRANCHES! of 4
echo.
echo   TWO THINGS ARE STILL YOURS TO DO ON THE WEBSITE:
echo     1. Set the default branch to main.
echo     2. Give the Claude GitHub App access to the new
echo        repository, or no session can push to it.
echo.
echo   AND ONE THING TO KNOW: every commit now has a new
echo   identifier, because moving files through history
echo   rewrites it. Old identifiers still work, in the old
echo   repository, which is why that one is kept.
echo.
echo   THE OLD REPOSITORY IS UNTOUCHED AND STILL WORKS.
echo   Do not stop using it until a full run has gone
echo   through on the new one.
echo   ==================================================
echo   DONE. lfs=!NOWLFS! branches=!REMOTEBRANCHES!/4 >> "%LOG%"
goto END

:KEEP
git branch --track %1 "origin/%1" >> "%LOG%" 2>&1
if errorlevel 1 echo       WARNING: could not keep %1, it may not exist upstream
if errorlevel 1 echo       WARNING could not keep %1 >> "%LOG%"
goto :eof

:NOGIT
echo   STOPPED: Git is not installed, or not on the path.
echo   STOPPED no git >> "%LOG%"
goto END
:NOLFS
echo   STOPPED: Git Large File Storage is not installed.
echo   Install it from git-lfs.com, then run this again.
echo   STOPPED no git-lfs >> "%LOG%"
goto END
:NOABOVE
echo   STOPPED: the installed Git Large File Storage is too old. It cannot
echo   select files by size, which is the whole method here. Update it from
echo   git-lfs.com and run this again.
echo   STOPPED git-lfs has no --above >> "%LOG%"
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
:MIGRATEFAIL
echo   STOPPED: the move into Large File Storage failed. See the log.
echo   NOTHING WAS SENT ANYWHERE. The old repository is untouched.
echo   STOPPED migrate failed >> "%LOG%"
goto END
:NOTHINGMOVED
echo   STOPPED: the move reported success but NOT ONE FILE ended up in Large
echo   File Storage. That is the failure that looks like success, so it is
echo   treated as a failure. Nothing has been sent. See the log.
echo   STOPPED zero files in LFS after migrate >> "%LOG%"
goto END
:FEWERMOVED
echo   STOPPED: fewer files ended up in Large File Storage (!NOWLFS!) than
echo   were over 2 MB beforehand (!BIG!). Nothing has been sent. See the log.
echo   STOPPED fewer moved than expected >> "%LOG%"
goto END
:NOATTRS
echo   STOPPED: no .gitattributes was written, so future clones would not know
echo   to keep using Large File Storage. Nothing has been sent.
echo   STOPPED no gitattributes >> "%LOG%"
goto END
:PUSHFAIL
echo   STOPPED: sending main failed.
echo   THE MOST LIKELY CAUSE is the Large File Storage allowance: this sends
echo   about 1.1 GB and the included allowance may be smaller. Check the
echo   billing page. The second most likely cause is that this PC cannot
echo   write to the new repository yet.
echo   Nothing is lost. The old repository is untouched and the work folder
echo   can be pushed again once the cause is fixed.
echo   STOPPED push main failed >> "%LOG%"
goto END
:PUSHBRANCHFAIL
echo   PARTIAL: main arrived but at least one of the other three branches did
echo   not. The atlas and the message channel live on those, so this is not
echo   finished. See the log.
echo   PARTIAL other branches failed >> "%LOG%"
goto END
:PARTIAL
echo   PARTIAL: only !REMOTEBRANCHES! of the 4 branches are at the new home.
echo   PARTIAL remoteBranches=!REMOTEBRANCHES! >> "%LOG%"
goto END

:END
echo.
echo   Log written to: %LOG%
echo.
pause
endlocal
