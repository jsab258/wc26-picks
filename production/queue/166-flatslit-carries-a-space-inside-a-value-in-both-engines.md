line: instrument (the verdict surface)
spec: SceneLine's `flatsLit=0/0 nothing-to-light` becomes a single token
  (`flatsLit=0/0/nothing-to-light` or equivalent), in BOTH engines, with the selftest
  assert changed in the same commit, and the token walk extended to cover the scene
  line so a spaced value cannot return.
acceptance: every token on the scene line is a key=value with no space in its value,
  proved by a walk over the line rather than by a spot check, and the two engines still
  print comparable strings
max_sessions: 1
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-09. Amendment A10 of
  game-design/decision-2026-09-09-the-twelve-clauses-and-the-buried-grate.md,
  declared by the builder that found it while landing something else.
  THE FAULT IS THE ONE THE STUDIO HAS ALREADY BEEN BITTEN BY: every reader splits on
  whitespace, so a grep for flatsLit= returns 0/0 and the words are stranded in a
  separate token. .claude/rules/instruments.md carries the rule and five values were
  fixed for it on an earlier pass; this one was missed because the selftest ASSERTS THE
  SPACED FORM, so the guard pins the bug.
  WHY IT IS FILED RATHER THAN FIXED IN PASSING: both engines read that line and the
  existing row pins the exact string, so the emit, the assert and the token walk have
  to move together or the two engines stop being comparable.
  A CORRECTION TO THIS ITEM'S OWN FIRST DRAFT, made the same night. The resident wrote
  here that the selftest now PRINTS the spaced token rather than asserting it. That was
  taken from a builder's report and it is false, refuted by a director reading the file:
  ue-probe/tests/vignette-spec-test.cpp line 313 is a Check that ASSERTS
  "flatsLit=0/0 nothing-to-light" and pins it, and the token walk at 291 to 307 covers
  the SHOT line only and has never read the scene line. So the guard pins the bug and
  nothing prints a warning beside it, which makes this item slightly more urgent than
  its first draft implied and is exactly why a report is not evidence.
