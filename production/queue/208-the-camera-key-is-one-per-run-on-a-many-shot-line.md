line: instrument
spec: VignetteShot.cpp holds a single GCamLine that the shot loop overwrites, and no shot
  line carries any camera key, so the camera a frame was taken from is a PER-SAMPLE fact
  printed on the WHOLE-RUN line, last-wins. Move it: each shot line carries its own camera
  identity and pose, and the run line keeps only what is true of the run.
acceptance: one committed run prints a camera key on every shot line with its denominator,
  tools/frame-shadow-probe.py binds strictly against any shot in that run regardless of the
  order they were taken, and a planted run whose shot order is reversed reads identically.
max_sessions: 1
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-09, item E of game-design/decision-2026-09-09-ruling-the-sun-ladder.md.
  MEASURED, NOT ARGUED: running the committed probe against today's frames gives
  camBind=REFUSED probeStatus=REFUSED probe=nothing-measured on cam_A, because the last
  camera placed in that run was cam_hook. The tool fails closed, which is correct; the
  verdict is what cannot answer it.
  IT IS THE SAME RULE THE SAME SESSION APPLIED CORRECTLY ONE BRACKET AWAY. The sun's four
  reads were split into whole-run keys on the run line and per-sample shotSun*Read keys on
  each shot line, deliberately, for exactly this reason. The camera was left as it was.
  A RUN WHOSE SHOT ORDER DECIDES WHETHER A TOOL CAN READ IT IS ONE REORDERING FROM SILENCE.
