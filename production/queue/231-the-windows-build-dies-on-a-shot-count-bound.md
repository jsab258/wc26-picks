line: instruments
spec: stage-vignette-scene's shot bound asserts what the scene must CONTAIN
  rather than what it must contain ONLY, so adding a probe row stops killing
  the Unity Windows build.
acceptance: the selftest green with 25 shots in the file, and red on a scene
  that is MISSING one of the four judged pairs
max_sessions: 1
status: READY 2026-09-09 23:45Z. PRE-EXISTING and found by a builder that
  refused to loosen it, which is the right instinct and the reason it is a
  queue item rather than a diff.

  THE FAULT. tools/stage-vignette-scene.py --selftest asserts len(shots) == 4.
  The committed scene has carried eleven since the ladder landed and carries
  twenty five with the grid. Its step in .github/workflows/ledger-build-windows.yml
  is NOT continue-on-error, so THE UNITY WINDOWS BUILD DIES at "Stage the D1b
  vignette scene", and it has been dying since before tonight's batch.

  WHY THE BOUND WAS RIGHT WHEN IT WAS WRITTEN and is wrong now: the shot list
  WAS the four judged pairs. It became a working surface the moment probe rows
  were allowed into it, and an equality bound on a set the project deliberately
  grows is a bound that fails on success.

  THE REPAIR IS NOT TO RAISE THE NUMBER. Raising 4 to 25 buys one more day and
  fails on the next probe row, and it would also stop asserting the thing that
  matters. Assert that the four judged pairs are PRESENT, and let the file
  contain whatever else a run needs. Rejecting fixture: a scene MISSING one of
  the four, which must go red.

  THE PRECEDENT WORTH KEEPING, and it is why this was filed rather than fixed
  in the same diff that tripped it: the builder that hit this refused to change
  the bound, on the ground that changing a guard's bound to fit your own diff
  is the one move that erodes a gate. That is exactly right, and it is the
  second time tonight the studio held that line: 1625 insertions were reverted
  earlier rather than edit two tests into passing.
