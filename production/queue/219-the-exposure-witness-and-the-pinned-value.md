line: instrument
spec: Snapping the auto-exposure RATE makes the rig deterministic; it does not make it
  photometric. At speed 10000 adaptation is instant but still automatic, so a cross-condition
  delta is still the radiance change after auto exposure fought part of it back, biased the
  same way as before. Read band.skyCentre across conditions ON cam_hook SHOTS ONLY as a free
  exposure witness, print the series, and set a pinned exposure value from it.
acceptance: one committed run prints the witness series across conditions, and the pinned
  value cites the run and the condition it was read from.
max_sessions: 1
status: BLOCKED on queue 194. The witness only works on a camera whose band.skyCentre is
  actually sky: 194 records that the fixed rectangle is mostly rooftops at fovV 60 (cam_A,
  cam_B) and sky only at 39 (cam_hook). Using it on the wide cameras would repeat tonight's
  struck reading.
  RULED 2026-09-09 in game-design/decision-2026-09-09-ruling-the-settled-exposure-and-the-two-lanes.md.
  NO NEW CODE AND NO BOUND TONIGHT: the witness is a key that already exists, read on the one
  camera it is valid for, and the bound comes after the series, per rule 2.
  WHY THE RATE SNAP WAS STILL RIGHT: pinning the VALUE needs a number nothing has measured,
  because the adapted exposure is a render-thread quantity this process never reads. Rate
  first, series second, value third, in that order.
