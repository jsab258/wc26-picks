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

  CAUSE READ 2026-09-10 04:20Z, OFF THE FILE CI COMMITTED rather than off the
  job log or an argument. game-design/agent-reports/machine-report.txt at
  commit 1fcc91bd:

      spec file=tools\imagegen\compare-hook-2026-09-09-pass2.json
        source=--spec schema=2 itemsInSpec=4
      REFUSED TO START: prompts.json is not usable as it stands.
      REFUSED: 0 written, 0 skipped, 0 failed, 0 attempted of 4 in the batch

  THE SPEC ARRIVED. source=--spec and itemsInSpec=4 say the pass-2 file was
  found, parsed and its four items selected. So the plumbing landed on
  2026-09-09 works, and the refusal is downstream of it.

  THEN IT REFUSED ON A FILE IT WAS NOT ASKED TO USE. The message names
  prompts.json, which is the 45-item SHIPPED LIBRARY and is precisely the file
  this whole comparison exists to avoid touching.

  TWO CANDIDATES AND THE EVIDENCE DOES NOT YET SEPARATE THEM. Either the
  validation gate reads prompts.json unconditionally while the loader honours
  --spec, which is the same two-parties-one-agreement shape as the sun and the
  bootstrap; or the gate validated the file it was given and its message names
  prompts.json by a hardcoded string, in which case the fault is the message
  and the spec is genuinely bad. THE SECOND IS TESTABLE IN THE CONTAINER FOR
  NOTHING: run the validator on both files here and see which one refuses.

  WHAT MAKES THE FIRST MORE LIKELY AND IS NOT PROOF: run 5 drew four pictures
  from a sibling spec built the same way, hours earlier, with prompts.json
  unchanged between the two runs.

  RULE 6 EITHER WAY. Something checks a file nobody asked it to check, or
  something reports a filename it did not read. Both are cheap to fix and
  neither was visible from the exit code, which is why .claude/rules/ci.md says
  verify a job's EFFECTS.

  THE CONTAINER TEST WAS RUN AND IT SEPARATED NOTHING, recorded because a test
  that proves nothing is worth naming so the next session does not repeat it.
  Both files were put through `plan --dry-run` here and NEITHER refused. That
  is not evidence that both are fine: the run's own step line reads
  selftest=success,probe=success,GENERATE=failure, so the refusal lives in the
  GENERATE path and `plan` never reaches it. I tested the wrong entry point,
  which is the instrument fault this project keeps writing rules about.

  THE TEST THAT WOULD SEPARATE THEM is the generate path with the model absent,
  far enough in to hit the validation and no further, or simply a grep for the
  string "is not usable as it stands" to find which file the emitter was
  holding when it printed. THE SECOND COSTS NOTHING AND SHOULD BE FIRST.

  SETTLED 2026-09-10 04:30Z, AND THE FAULT IS THE RESIDENT'S. The committed
  manifest names it per item, four of four:
    "the POSITIVE prompt still says ['no'] - an exclusion belongs in
     `negatives`, because a diffusion model reads the noun and draws it. That
     is what put a sign board on wall_soot_brick."
  THE CORRECTION PASS, WRITTEN TO FIX LETTERING, ASKED FOR "no text" TWICE IN
  THE HALF OF THE PROMPT THAT CANNOT EXPRESS "no". The guard is right, it names
  its own precedent, and it refused before spending a minute of GPU. Fixed by
  moving both exclusions into `negative`; the token is now absent from 4 of 4
  positive prompts and present in 4 of 4 negatives.

  THE TOOL'S ONE REAL FAULT, fixed here: the refusal message hardcoded the
  string "prompts.json" and therefore named the wrong file on every run given
  a --spec. It now names no file rather than a wrong one.

  AND THE DIAGNOSIS WAS SLOWED BY THE READER, NOT BY THE TOOL. The per-item
  reasons WERE printed to the log and WERE in the committed report. The
  resident's own grep filtered that file to lines matching refus, exit, spec,
  error, fail and skip, and the four lines that carried the answer matched none
  of those words, so a filter written to find the cause hid it. Same family as
  the standing rule that any cap in a log-extraction step must announce when it
  bites: A FILTER IS A CAP ON WHICH LINES EXIST.
