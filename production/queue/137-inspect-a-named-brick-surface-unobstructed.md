line: production (the Unreal emitter, Phase C)
spec: Jafar 2026-09-06, "Inspect the identified brick surface in an
  unobstructed frame before claiming that specific check passed; whole-frame
  colour cannot establish which material appears on that surface."
acceptance: a named brick_red piece, proven unobstructed by a z-ordered
  coverage test at the sampled point, measured against brick_red.jpg's R/B
  1.290 and chroma mean 31.9, with the piece name and the coverage result
  printed beside the reading
max_sessions: 1
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-06. Small, and it closes the one check left open by the
  street's success.

## Why this exists

Queue 123's third acceptance reading was measured through a pane of glass one
metre from the camera while the brick it named sat sixteen metres behind. It
is INVALID rather than failed, and Jafar has ruled that it must not be
reported as either until a brick surface is inspected unobstructed.

The two readings that carried the street are the colour control quad and the
whole-frame chroma, and neither says which material is on which surface. That
is precisely what this item measures and what nothing currently does.

## What it must do

Pick a brick_red piece and PROVE it is the nearest coverer at the sampled
point with the same z-ordered box test that found the glass, printing the
piece name and what else covers that point. Then measure, and compare against
the source texture rather than against a remembered figure.

## The rule this is an instance of, and it cost a whole reading

A SAMPLE WINDOW CHOSEN WHILE EVERYTHING IS BROKEN CAN ENCODE THE BREAKAGE. All
six surfaces rendered the same grey, so glass and brick were indistinguishable
and any window seemed to work. The window only became wrong when the fix made
the materials different from each other.

So a baseline needs its own accepting case: something that would have looked
different if the window were pointed at the wrong thing. Here that would have
been one z-ordered coverage test at the moment the window was chosen, which
takes seconds and was not done.
