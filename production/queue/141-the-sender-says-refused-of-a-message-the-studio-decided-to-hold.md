line: production (the channel to Jafar)
spec: found 2026-09-06 by the resident, measured in
  production/outbox/README.md: the gate passes the two annotated legacy
  messages and the sender refuses them.
acceptance: tools/runner/outbox.py treats a file named on
  tools/producer-check.py:LEGACY_LINK_RULES as gate-only, never sent,
  and prints it under its own count (heldHistorical=N) beside refused=,
  with a record on the pc-inbox branch that says held-historical rather
  than a register clause; the selftest plants a listed name and asserts
  it is neither sent nor counted as refused, and plants an unlisted
  over-cap name and asserts it still is refused
max_sessions: 1
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-06. Monday. Ruled in game-design/decision-2026-09-06-
  ruling-delivery-batch-map-availability-and-outbox.md section 6: the two
  files are NOT sent, by decision. This item makes the sender say so in
  the right word.

## Why not teach the sender the retired rules

Because the ruling is that they do not go. A sender that graded them
under the retired rules would send them, marked, which is the option the
director refused: both bodies are superseded and the decision in one is
already ruled. The remaining fault is a word: refused is what the
register says of a bad message, and these are good messages the studio
decided not to deliver.
