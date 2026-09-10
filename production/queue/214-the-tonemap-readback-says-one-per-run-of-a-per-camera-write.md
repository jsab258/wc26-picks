line: instrument
spec: VignetteShot.cpp writes the auto-exposure speed override inside PlaceCamera, which the
  shot loop calls per shot, but prints tonemapStat=last-camera-placement/one-per-run on the
  scene line. The action is per-camera and its only committed evidence is not. Split it the
  way the sun keys were split: whole-run facts on the run line, a per-sample readback on each
  shot line.
acceptance: every shot line carries its own override readback, the run line carries none, and
  a planted run where one camera's override fails to land reads as one shot differing rather
  than as a whole run.
max_sessions: 1
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-09, ruled in game-design/decision-2026-09-09-ruling-the-settled-exposure-and-the-two-lanes.md as the FIFTH instance in one batch of the fault that
  batch was fixing. The same session split the sun's four reads correctly into whole-run and
  per-sample, split the camera correctly under queue 208, and left the tonemap readback
  one-per-run one bracket away from both.
  IT IS NOT COSMETIC. The override is what makes the rig deterministic, so a run where it
  landed on ten cameras and missed one would print a single reassuring line and the frame it
  missed would be the outlier somebody later explains as noise.
