line: infrastructure (D1 probe, measurements a and b)
spec: production/d1-probe/plan.md, the corrected section
acceptance: a dispatchable UE workflow that builds on ledger-pc, captures a still, commits it and a timed step breakdown to the evidence channel; first green run recorded
max_sessions: 3

Write .github/workflows/ledger-build-unreal.yml, mirroring
ledger-build-windows.yml in shape and in evidence discipline: runs-on
[self-hosted, ledger-pc], workflow_dispatch only, per-step timeouts, a
verdict file naming its commit on line 1, stills staged BY NAME rather than
by directory, and a NO RUN marker when it measured nothing.

This is what puts the UE half of D1 on the machine without asking Jafar for
anything. It carries the same two rules the Unity workflow learned the hard
way: a run that rendered nothing must not commit its checkout's stale
stills as its own, and the verdict must say which commit it came from.

DEPENDENCIES ON THE MACHINE, to check in the first dispatch rather than
assume: UE 5.8.2 is installed; a C++ toolchain may not be. If the build
step fails for a missing toolchain, that is a finding for measurement a
(setup cost), not a broken workflow, and it is recorded as such.

status: DONE 2026-09-01, run 13. The workflow builds, cooks, stages,
        packages and runs the probe on ledger-pc, and the golden test passes
        against the PACKAGED artifact: 1221 rows, 0 mismatches. Thirteen runs;
        every failure was diagnosed from a committed file and none from a log
        tail. Numbers in production/d1-probe/measurements.md.

        The quality-ladder question, asked at close: the first working result
        would have been the run-11 build with the test passing on the compile
        output. Running it against the packaged artifact instead is the better
        available rung and it was taken, because a compile output is not what
        anybody would ever be given. The next rung is task 007, the evidence
        channel, and it is queued rather than folded in here.
