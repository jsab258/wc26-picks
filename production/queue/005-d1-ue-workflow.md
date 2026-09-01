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
