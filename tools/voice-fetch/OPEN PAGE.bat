@echo off
REM LEDGER voice casting - reopen the listening page.
REM
REM The page is a file on disk, not a server, so closing the tab loses
REM nothing and re-running "1 LISTEN.bat" would re-stream the corpus for
REM no reason. This just opens it again.
cd /d "%~dp0"
set "PAGE=%~dp0ledger-voices-out\listen.html"
if not exist "%PAGE%" goto :nopage
start "" "%PAGE%"
echo.
echo  Opened %PAGE%
echo  Write your picks into ledger-voices-out\picks.txt, then run
echo  "2 INSTALL.bat".
echo.
exit /b 0

:nopage
echo.
echo  No page at %PAGE%
echo  The fetch has not produced one yet - run "1 LISTEN.bat" first.
echo.
pause
exit /b 1
