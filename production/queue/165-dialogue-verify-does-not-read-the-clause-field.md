line: instrument (the dialogue bank's own gate)
spec: tools/dialogue-verify.py scores the `clause` field alongside `text`: the rung
  check, the repetition bound and the "player" screen all run over clauses, and the
  clean line prints both denominators rather than one.
acceptance: a clause that repeats another clause, names a rung it has not reached, or
  says "player" turns the tool red, and the clean line says how many clauses it read
max_sessions: 1
status: READY 2026-09-08. Filed from a builder's own declaration while landing the
  twelve clauses of queue 157.
  THE GAP: the tool scores ln["text"] only. Twelve clause values now sit on the
  witness_summary rows and the tool reports "clean - 0 finding(s) over 24 line(s), 276
  pair(s) compared" without having read one of them. The result is TRUE and its
  denominator is the wrong set: a clean run over the half that did not change. That is
  rule 3b pointed at a gate rather than at a zero.
  WHAT EXISTS INSTEAD, and why it is not enough: the builder ran the tool's own scorer
  over the twelve by hand and recorded the numbers in
  production/specs/dialogue-crime-witness-v1.md. 0 rung-name findings over 12 clauses,
  0 of 66 clause pairs at or over the 0.60 repetition bound with a worst of 0.32, 12 of
  12 lowercase-initial, 0 of 12 with an interior or trailing stop, 0 of 12 saying
  "player". A hand-run number is evidence for the person who ran it and for nobody
  afterwards, which is the same objection this studio made to a one-shot cross-engine
  harness on the same night.
  RULE 5b APPLIES TO THE CHANGE: the accepting case is the live bank, whose twelve
  clauses must stay green, and the rejecting fixture is synthetic.
