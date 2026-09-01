# tools/runner: TWO DIFFERENT RUNNERS, and the name is the problem

READ THIS FIRST. This project has two things called "the runner" and
confusing them cost a wrong critical path on 2026-09-01:

1. THE CI BUILD AGENT. C:\actions-runner-ledger on Jafar's PC, label
   `ledger-pc`, a GitHub Actions self-hosted runner listening for jobs. It
   is what the numbered .bat files here SET UP. Dispatched remotely, it
   builds, runs the sim, captures stills and commits them back, and it
   needs nothing from Jafar. This is how machine-side work has happened
   since 22 Aug.
2. THE NIGHT LOOP. run-night.bat and run-night.ps1 here, written
   2026-08-31: a local loop launching Claude sessions against
   production/queue/. For continuous autonomous development. NOT required
   for CI work, and not a prerequisite for anything the build agent can do.

If a task says "the runner", it is ambiguous and should be rejected at
spec until it names which one.

The NUMBERED bats and the .txt notes are the v1 Unity build-runner setup for
the self-hosted CI runner (ledger-pc): untouched, still what CI builds run
on. The files below are the v2 OVERNIGHT LOOP, a different machine-sized
thing that happens to share the folder because runner.md names these paths.

# The night runner (ledger-v2/studio-v2/runner.md made concrete)

Written on the container, executed on Jafar's Windows PC. The PowerShell has
never run where it was written (no PowerShell in this container; the verify
footer names that lint NOT CHECKED), so the first Windows run is its
accepting test and should be watched, per rule 5b.

- run-night.bat   one click, manual start
- run-night.ps1   the loop; -Register adds the 23:30 Task Scheduler entry
- dispatch.md     the fixed prompt every worker session receives
- production/STOP kill switch, checked between iterations

To validate on the PC, in this order: queue ONE trivial task, run
run-night.bat, watch the whole iteration; only then -Register the schedule.
The runner never touches main; it works on night/YYYYMMDD and the
integrator merges what passes gates. Escalations (email, dead-man ping)
stay off until wanted, per runner.md.
