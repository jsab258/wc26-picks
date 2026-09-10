line: instrument
spec: tools/workflow-size.py prints "17 workflow(s)" while .github/workflows holds 18. Its
  check() does `if not found: continue` and its RUN_START only matches `run: |` or `run: >`,
  so a workflow whose run steps are all single-line is dropped in silence and the printed 17
  reads as the population. Make the printed count say what it examined and what it dropped,
  by name.
acceptance: the done line carries examined, dropped and the dropped names, and a planted
  workflow with only single-line run steps prints as dropped rather than vanishing. A run
  that examined nothing prints the words "nothing measured".
max_sessions: 1
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-09. MEASURED, not inferred: files=18 reported=17
  dropped=ledger-core-tests.yml. Found by a builder reading the other workflows while fixing
  the art lane's missing PATH bootstrap, which was the same fault one level up: a count that
  cannot tell "17 of 17" from "17 of 18".
  THE GUARD ITSELF IS SOUND and this item does not touch it. A single-line run step cannot
  approach the 23k limit, so nothing dangerous is being missed. What is wrong is only the
  number beside it, which is the half a reader trusts.
