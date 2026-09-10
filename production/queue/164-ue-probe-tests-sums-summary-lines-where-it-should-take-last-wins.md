line: instrument (the studio's own gate)
spec: ledger/verify.py ue_probe_tests takes LAST-WINS PER BINARY over the two summary
  regexes rather than summing every match on every line.
acceptance: a binary printing two summary lines contributes one total, and a line
  matching both shapes counts once, proved by a fixture in both directions
max_sessions: 1
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-08. Filed by the director ruling
  game-design/decision-2026-09-08-queue-147-the-composed-telling-and-the-clause-the-bank-never-had.md,
  amendment A1b, which put the warning comment in beside the regexes as dictated text
  and left the fix to this item.
  HOW IT WAS FOUND: the queue-147 builder's first wiring of a fourth binary read 2972
  checks, because its own summary line matched both regexes. It corrected the total to
  2851 by changing the test file's print, which means the convention that keeps the
  two shapes disjoint currently lives in the TEST FILES and not in the reader. A
  convention nothing validates is the class of fault this project keeps finding.
  THE SHAPE OF THE RISK: a gate that OVERCOUNTS reads as more coverage than exists,
  and it is the quietest direction to fail in, because a rising number looks like
  progress.
