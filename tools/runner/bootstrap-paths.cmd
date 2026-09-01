@echo off
REM THE SELF-HOSTED PATH BOOTSTRAP. ONE IDEA, ONE IMPLEMENTATION.
REM
REM It existed twice, inline in two workflows, and it drifted the first day
REM it was duplicated: the probe's copy dropped the pwsh half and the
REM explicit exit, and that workflow's first run died on "pwsh: command not
REM found" with nothing else to say. One idea in two implementations, and
REM the one nobody looks at is the one missing a line.
REM
REM THE DIAGNOSTIC MESSAGES ARE THE DELIVERABLE, not the PATH appends. Each
REM one names the thing to run on the machine when a tool is genuinely
REM absent, and that is the part a person acts on. Do not shorten them.
REM
REM Callers use `call`, so control comes back and the exit code propagates:
REM     shell: cmd
REM     run: |
REM       call tools\runner\bootstrap-paths.cmd
REM       exit /b %ERRORLEVEL%
REM This step must therefore run AFTER checkout, which is a change for the
REM probe workflow, where it used to run first. actions/checkout is a
REM JavaScript action and needs neither bash nor pwsh, so the reorder is
REM safe; nothing between them wants either tool.
where bash >nul 2>nul
if not errorlevel 1 goto :bashok
if exist "C:\Program Files\Git\bin\bash.exe" (
  >>"%GITHUB_PATH%" echo C:\Program Files\Git\bin
  echo bash found at C:\Program Files\Git\bin and put on the job PATH
  goto :bashok
)
echo NO bash ON THIS MACHINE - Git for Windows normally provides it.
echo Reinstall Git for Windows on this runner, then dispatch again.
exit /b 1
:bashok
where pwsh >nul 2>nul
if not errorlevel 1 goto :pwshok
if exist "C:\Program Files\PowerShell\7\pwsh.exe" (
  >>"%GITHUB_PATH%" echo C:\Program Files\PowerShell\7
  echo pwsh found at C:\Program Files\PowerShell\7 and put on the job PATH
  goto :pwshok
)
if exist "C:\LedgerTools\pwsh7\pwsh.exe" (
  >>"%GITHUB_PATH%" echo C:\LedgerTools\pwsh7
  echo pwsh found at C:\LedgerTools\pwsh7 and put on the job PATH
  goto :pwshok
)
echo NO pwsh ON THIS MACHINE - the build and verdict steps run on it.
echo Run "tools/runner/3 FINISH THE BUILD MACHINE.bat" once on this
echo runner, then dispatch again.
exit /b 1
:pwshok
echo tool PATH bootstrap done.
REM Explicit, because cmd exits with the LAST-SET errorlevel and echo/goto
REM never clear one: a failed `where` above left 1 behind, and run
REM 32595203790 did every append right, printed done, and still reported
REM failure - skipping the whole build after it.
exit /b 0
