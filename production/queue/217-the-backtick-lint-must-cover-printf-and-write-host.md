line: instrument
spec: A backticked identifier inside a double-quoted shell string is executed by the shell.
  It has now happened three times in this repository. Build the lint, and cover printf and
  Write-Host as well as echo, in workflows and in shell scripts.
acceptance: the live tree passes with the count of strings examined printed, and a planted
  backticked identifier inside a double-quoted echo, printf and Write-Host each go red.
max_sessions: 1
status: READY 2026-09-09, ruled in game-design/decision-2026-09-09-ruling-the-settled-exposure-and-the-two-lanes.md after the third instance: a guard's own error message
  read "Add an `out:` line" and the shell ran out: and printed "out:: command not found".
  THE THIRD INSTANCE BUYS A LINT, NOT ANOTHER PARAGRAPH. CLAUDE.md already carries the
  sentence, the sentence has been read by every session since, and the fault happened again
  inside a guard written to prevent a different silent failure. A rule that has been read and
  broken three times is a rule that needs an instrument.
  IT WAS CAUGHT BY RUNNING THE GUARD, not by reading it, which is also the argument: the lint
  is cheaper than the run that finds it.
