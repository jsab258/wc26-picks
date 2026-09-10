line: art (the visual bar)
spec: The cause of imagegen run 7's generate failure is READ from the step's
  own log rather than guessed, and the pass-2 Hook draw is re-run.
acceptance: the exit code named, the cause stated with the line that proves
  it, and four pass-2 pictures banked
max_sessions: 1
status: READY 2026-09-09 23:20Z. FILED WITH THE CAUSE DELIBERATELY UNNAMED,
  because it was not measured and a plausible cause written down tonight is a
  claim the next session would inherit as a fact.

  WHAT IS ESTABLISHED, all of it read rather than inferred:
    run 7 on fe13e915, steps generate=failure, everything else success
    the job ran 20:35:31Z to 20:36:56Z, about 85 seconds end to end, where
      run 6's generate step alone took about ten minutes
    selected=4 inSpec=4 limit=4, and wroteThisRun=0 failed=0 checkedThisRun=0,
      so it SELECTED FOUR ITEMS AND ATTEMPTED NONE
    BATCH_SETTINGS_OK=yes with all five settings correct in the env block, so
      the refuse-guard exits 7 and 8 are RULED OUT
    the pass-2 spec is structurally identical to the pass-1 spec that worked:
      same 9 top-level keys, same item keys but for a dropped comment field
    the verdict refused correctly and said so: batchStatus=REFUSED,
      imagegenVerdict=NO-RUN, and "Nothing older is being read as this run's
      answer". The instrument behaved.

  WHAT IS NOT ESTABLISHED: which exit code generate returned. The workflow
  prints a menu of eight and the step's own log prints specAsked beside
  specPassed. NEITHER WAS READ. That is the whole next step and it is cheap.

  A NEAR MISS WORTH THE LINE, because it is the reason this item names no
  cause. The committed machine report says "vulkan drivers registered: 0" and
  "loader present but NO Khronos key - the display driver registered no Vulkan
  device", with a Parsec Virtual Display Adapter sitting at GPU [0] ahead of
  the AMD Radeon RX 6700. That reads exactly like the answer and it is NOT:
  RUN 6 SUCCEEDED WITH THE IDENTICAL TWO LINES, and it banked four pictures at
  154 seconds each. The reading is the same on a run that worked and a run that
  did not, so it separates nothing. It was one edit away from being filed as
  the cause.

  THE RULE THIS OBEYS is the one in .claude/rules/ci.md that the studio wrote
  after producing four explanations for a silent channel in one night: THE
  ENTRY POINT IS CHEAPER THAN THE ARGUMENT, and it answers rather than narrows.
  Read the generate step's log slice, then act.
