line: studio (a gate that can pass a failing tool)
spec: found in passing by the agent running the sweep, while checking its own
  call sites.
acceptance: the gate fails when the study selftest fails, proven on both
  outcomes with the accepting case first
max_sessions: 1
status: READY 2026-09-06. One line, and it is the shape this project keeps
  finding: a gate that reads a string and ignores the verdict.

## The finding

`ledger/verify.py` line 1794 matches the beat-identity line out of the
stranger test's output and never looks at the EXIT CODE. The tool now runs two
suites, the beat-identity selftest and the study selftest, and prints a line
for each. So the study selftest can fail while the gate reads the other line
and passes.

A regex that keeps matching while the thing it summarises has failed is how a
footer becomes a noun. This project has recorded that sentence before, about a
different gate, and here it is again in a tool written this morning.
