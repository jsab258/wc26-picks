line: instrument
spec: band.skyCentre must measure sky or stop being called sky. It is a fixed pixel
  rectangle (512/0/768/90) read on every shot, and the cameras it is read on do not
  share a field of view: cam_A and cam_B render at fovV=60.0, cam_hook at 39.0. On the
  wide cameras that rectangle is mostly rooftops. Replace it with a per-column roofline
  search that measures only above the roofline, and ship the denominator: how many
  columns found one, and the words "nothing measured" when none did.
acceptance: on ONE committed run, the sky number for cam_A and cam_hook answers the same
  question, the per-column found-count prints beside it, and a planted frame with no sky
  visible at all prints nothing measured rather than a number.
max_sessions: 1
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-09. FOUND BY BEING MISLED BY IT, which is the only reason it is
  filed: the director read cam_A's 0.8459 as the rung-1 camera's sky and reported the fog
  signature gone. The rung-1 camera's own value on the same run is 0.9323 at spread
  0.0078, seventy times flatter than cam_A's 0.5434, because cam_A's spread is BRICK.
  THE VERDICT ALREADY SAYS SO and that is the sharp half of this item:
  bandStat=per-frame-geometric-bands/named-for-what-they-cover-not-for-what-is-in-them.
  The instrument declared its own limit in a key, on the same line, and the limit was
  read past anyway. A declared limit that only a careful reader survives is a limit that
  will be read past again, so the fix is the measurement and not a longer note.
  DO NOT SET A BOUND IN THIS ITEM. Print the series over the five committed shots first,
  per rule 2, and let a later item read the number.
