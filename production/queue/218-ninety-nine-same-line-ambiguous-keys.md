line: instrument
spec: tools/verdict-dupkeys.py reports 99 same-line and 16 cross-line ambiguous keys over the
  vignette verdict's record lines. Reduce them, or rule each survivor as deliberate with its
  reason, so the count means something.
acceptance: every remaining ambiguous key is named with why it is allowed, and the count
  prints beside the number examined.
max_sessions: 2
status: READY 2026-09-09, ruled in game-design/decision-2026-09-09-ruling-the-settled-exposure-and-the-two-lanes.md. The number was stable across tonight's change (99 and
  16 over 59 lines against 99 and 16 over 58), so nothing regressed, which is exactly why it
  needs an owner: a number that never moves is a number nobody is reading.
