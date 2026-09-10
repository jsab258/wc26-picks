line: instrument (the gate that runs the other gates)
spec: ledger/verify.py's `_tool_selftest_run` takes a NAME, not a positional index into
  TOOL_SELFTESTS, and refuses loudly when the name is not in the table.
acceptance: renaming or reordering a row makes the wrong-tool case RED rather than green,
  proved on a planted reorder, and every existing row still runs its own tool
max_sessions: 1
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-09. Found by making the mistake it describes.
  MEASURED: three rows added the same morning were each off by one, so
  checkout_gate_selftest ran the wake queue, brief_selftest ran the checkout gate, and
  producer_day_selftest ran the brief. ALL THREE RETURNED TRUE. One tool would have been
  covered by nothing while the footer said it was covered.
  WHAT CAUGHT IT WAS THE LABEL IN THE OUTPUT, NOT THE RESULT. Every check passed and
  every count was a real count; the only thing wrong was which tool each number belonged
  to. A test asserting truthiness would have shipped it.
  THE TRAP IS THE INTERFACE. A positional index into a hand-edited tuple, typed twice
  hundreds of lines apart, with nothing asserting that brief_selftest runs the brief. The
  next person to add a row has less reason to suspect it than the person who just did.
