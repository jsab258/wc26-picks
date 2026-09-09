line: instruments
spec: Sweep the verdict surface for keys that are DIFFERENCES read across
  frames, and pair each with the ratio that survives an exposure multiplier.
acceptance: a printed census of difference-shaped keys with its denominator,
  every cross-frame one either paired with a ratio or annotated in place with
  why a difference is right there
max_sessions: 1
status: READY 2026-09-09 21:00Z. Blocked on nothing; it is a sweep, not a fix.

  THE GENERAL FORM OF TONIGHT'S FAULT. Commit b7ce9f61 established that no
  frame this rig takes is photographed at a settled exposure, so a whole-frame
  exposure multiplier k is in every number it prints. A luma DIFFERENCE scales
  with k. A luma RATIO does not. Every step, delta and "minus" key this rig
  prints is a difference, which is exactly why that commit had to void every
  cross-frame number at once.

  THE ONE NUMBER THAT MADE IT CONCRETE. The rung-1 frame's ground band carries
  p95/p05 = 1.61 against the reference photograph's 3.68. That single ratio
  states rung 1's fault, and no difference-shaped key on the same frame states
  it, because each of them is scaled by an exposure nothing reads back.

  WHAT THE SWEEP MUST NOT DO. It must not convert differences to ratios
  wholesale. A difference is RIGHT whenever both terms come from the same
  photograph and the question is "how far apart", and a ratio is undefined or
  unstable when the denominator approaches zero, which the night frames do
  (shotClipLoAll=26813/921600 on one ladder row). Each key gets a decision and
  a reason, not a rewrite.

  AND THE HONEST LIMIT ON THE RATIO ITSELF, which the next reader will need:
  this engine applies a TONEMAPPER, not a bare multiplier, so a ratio is only
  approximately invariant. Name the key so it cannot be over-read.
