line: engine and art, jointly
spec: Set the sun, and if the control row says the skylight owns the exposure also
  the sky, from the series queue 205 prints. THE LEVER IS NO LONGER A CONSTANT:
  kSunIntensityDay was never created and kSkyIntensityDay and kSkyIntensityNight were
  DELETED by queue 205, ruled 2026-09-09 in
  game-design/decision-2026-09-09-ruling-the-sun-ladder.md section 1. Both numbers now
  ride on the condition as sun_intensity and sky_intensity in
  production/specs/vignette-scene.json, so this item edits DATA in overcast_day and
  wet_night and edits no C++ constant. Both readers require both fields, so a value
  cannot be dropped rather than changed.
acceptance: four things, and the third is a debt booked by the ruling rather than a
  new ask.
  1. The condition's own note field cites the run number, the commit and the RUNG the
     value was read from, in the same file as the value. A JSON file has no comment,
     and the note field is where the provenance lives for every other number here.
  2. The next committed rung-1 frame meets queue 205's prediction: shadow-edge step at
     or above +0.027 where it now reads -0.0035, asphalt lit-minus-shadowed positive
     from -0.0131, and band.ground.p05 below 0.50 from 0.5776.
  3. THE HOOK FRAME IS RE-MEASURED, not inferred. Queue 205's ladder is six cam_A rows
     and cannot speak for cam_hook's pixels; until this item prints a cam_hook reading
     after the value lands, no document may quote an improvement to the rung-1 frame
     from run 38.
  4. THE LADDER ROWS ARE DECIDED, not left. The five ladder_ conditions and the control
     row cost six rendered frames and about 11 MB on every subsequent probe run. This
     item either removes them, with the read series preserved in its decision record,
     or keeps a named subset with the reason written beside it. Silence is not an
     option: rows kept by default are rows nobody chose.
max_sessions: 1
status: BLOCKED on queue 205 landing a READ series, not on queue 205 dispatching.
  IT IS BLOCKED ON PURPOSE AND THE BLOCK IS THE POINT: rule 2 says a bound is set from
  a printed series, and the series does not exist until run 38's frames are measured by
  tools/frame-shadow-probe.py with each frame's own three instrument checks quoted
  first. Landing a number here before then would be the exact fault the ladder was
  ordered to prevent.
