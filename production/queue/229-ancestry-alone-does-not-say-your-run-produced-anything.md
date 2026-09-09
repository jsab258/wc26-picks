line: instruments
spec: The watch rule in .claude/rules/ci.md gains its missing half, so a
  descendant commit carrying none of the payload cannot read as a landing.
acceptance: the rule states both halves, and the worked example in the
  casebook shows a false positive being rejected by the second half
max_sessions: 1
status: READY 2026-09-09 23:05Z. Measured by making the mistake tonight, in
  the same session that quotes the rule at builders.

  THE STANDING RULE, .claude/rules/ci.md: "Watch by ancestry (is there a landed
  run whose commit CONTAINS mine), never by branch movement or run name."
  Correct, and INCOMPLETE.

  WHAT HAPPENED. A watcher armed on commit fe13e915 fired on 17ec0904,
  "scheduled task install/verify from fe13e915". The ancestry test PASSED
  because that commit genuinely contains fe13e915. It carried zero files of the
  run's output. The watcher reported a landing and exited while the real run
  was still going.

  THE MISSING HALF. Ancestry answers "did something land AFTER my push". It
  does not answer "did MY RUN produce anything", and on a machine that commits
  its own housekeeping the two come apart routinely. The second test is the
  PAYLOAD: does the range from my sha to the landed head touch the paths this
  run was supposed to write. Both tests, and a landing needs both.

  IT IS THE SAME SHAPE AS THE RULE BESIDE IT. ci.md already says a run that
  measured nothing must say so and must not carry the previous run's files
  under its own name, because "the build carried the commit" and "the build
  measured anything" are different facts. THIS IS THAT SENTENCE APPLIED TO THE
  WATCHER RATHER THAN TO THE BUILD, and the studio wrote the first half and
  then read past it from the other side.

  ALSO WORTH THE LINE: the failing watcher was written by the resident who had
  quoted ci.md to two builders in the same hour.
