line: instruments
spec: The commit gate does not report failures it cannot substantiate, and a
  check that could not run says so instead of failing.
acceptance: verify.py run concurrently with heavy parallel work reports the
  same result as verify.py run alone, or names the checks it could not run and
  counts them separately from the checks that failed
max_sessions: 1
status: READY 2026-09-09 21:55Z. Measured tonight, both ways, by accident.

  WHAT HAPPENED. ledger/verify.py was run while four agents were concurrently
  reading files and running their own python and git processes. It reported
  THREE failures. Re-run individually and alone, two of the three PASS:

    test-blender-hash-parse   in verify: "NOTHING MEASURED (exit 1, no source
                              line named - it refused to look) FAIL ACCEPTING"
                              alone:     6 ok, 0 failed, 6 fixture(s) run
    ps-check                  in verify: "PWSH: a workflow step did not parse"
                              alone:     33 pwsh block(s), 0 problems
    vignette-spec-test        in verify: RED
                              alone:     GENUINELY RED, a builder is mid-edit

  No workflow file, no .ps1 and no blender file was modified in the working
  tree at all, which is checked and not assumed: git status names none.

  WHY IT MATTERS MORE THAN A FLAKE. verify.py IS THE COMMIT GATE. A gate that
  goes red for reasons the tree cannot explain is a gate that gets argued with,
  and a gate that gets argued with is a gate that eventually waves a real red
  through. Tonight it cost a diagnosis: two guards were nearly chased as bugs.

  AND THE ASYMMETRY IS THE WORRYING HALF. A spurious RED is visible and
  annoying. If contention can make a check report a failure it did not measure,
  the question nobody has asked is whether it can make one report a PASS it did
  not measure. Rule 3b: a check that could not run must print "nothing
  measured" and be counted apart from the checks that ran and failed. The
  blender line ALREADY prints those words and is still counted as FAIL
  ACCEPTING, so the words are there and the arithmetic does not use them.

  THE CHEAP HALF FIRST: make the footer count three populations rather than
  two, checks that passed, checks that failed, and checks that could not run,
  with the third named. That alone would have made tonight's read obvious.
