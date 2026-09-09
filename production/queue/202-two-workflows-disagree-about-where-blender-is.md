line: infrastructure
spec: tools/meshgen/probe-tools.ps1 is the canonical Blender search and takes PATH first;
  the art preview workflow now carries a second search that takes the newest globbed
  install first and PATH as a fallback. Two implementations of one idea that already
  disagree on precedence. Make the art lane read the committed answer
  (production/mesh-reports/blender-setup.txt, written by ledger-setup-msvc.yml on the
  machine itself) and print what that file claims BESIDE what it measured, so a divergence
  reads as a change to the machine rather than as a mystery.
acceptance: one run prints both the claimed path and the measured path with a same-or-
  differs word between them, and a planted disagreement prints as a difference rather than
  as a refusal.
max_sessions: 1
status: READY 2026-09-09. FOUND BY A FAILED RENDER, and the fault it cost was exactly this
  shape: ledger-setup-msvc.yml unpacked the portable zip to C:\LedgerTools\blender on 1
  September and wrote the path down; the art lane looked under Program Files and on PATH,
  found nothing, and printed candidatesTried=3/3, which is a count of our guesses and never
  a reading of his disk. Neither workflow named the other.
  A SECOND SEARCH WAS THE RIGHT CALL FOR THE REFUSAL and is not being undone here: calling
  probe-tools.ps1 from CI drags MSVC, CUDA and disk probing into a step whose job is to
  refuse informatively. What is missing is the COMPARISON, not the consolidation.
  The precedence disagreement is the part that will bite next: PATH first and glob first
  pick different binaries the day two are installed.
