line: art (the authored street)
spec: Measure, then decide. The next walk run prints the drainage grate's placed
  world-bounds top against the channel surface height at x=12, and whether any piece
  occupies the 0.4 m by 0.4 m footprint above it.
acceptance: the burial is confirmed or refuted by a placed-bounds reading rather than
  by arithmetic on a spec file, and if confirmed the street spec changes under its own
  review
max_sessions: 1
status: READY 2026-09-08, and it BLOCKS THE CLAIM that a walk clip shows Jafar's item
  2. It does NOT block the walk dispatch, because the run is how the measurement gets
  taken. Amendment A6 of
  game-design/decision-2026-09-08-queue-147-the-composed-telling-and-the-clause-the-bank-never-had.md
  section 7.
  THE ARITHMETIC, off production/specs/vignette-pieces.json, with y_m a centre and
  sy_m a full height, a convention two dustbin rows confirm (bin centre 0.395 height
  0.61 top 0.70; its lid centre 0.725 height 0.05 spanning 0.70 to 0.75):
    ground_east_channel       y -0.221766  sy 0.300  top -0.0718  spans x 0 to 42
    gully_dish_east           y -0.255     sy 0.300  top -0.1050
    prop_drainage_grate_01_0  y -0.0925    sy 0.015  top -0.0850  bottom -0.1000
  The grate's top is 13.4 mm BELOW the top of a continuous 42 m channel slab that
  spans x=12, and its bottom is 5 mm above the dish floor, itself inside that slab.
  The 1.43 degree cross-fall accounts for one or two millimetres, not thirteen. There
  is no CSG: nothing cuts a hole in the channel above the gully.
  SO AS SPECIFIED THE GRATE IS BURIED. A capsule at x=12 stands on the channel and
  never on the grate, and a frame cannot show it. Jafar's item 2, the drainage grate
  as a real mesh WITH COLLISION in a walk clip, cannot be satisfied by this placement
  even after the importer lands the asset.
  WHY NOTHING CAUGHT IT: this is the mirror of the placement rule in
  .claude/rules/instruments.md. A placement metric ships in two halves, distance to
  the datum and whether the datum exists under the footprint. propCentreWorstMm
  measures the distance and is blind to burial, which is how a piece sits 0.00 mm from
  where the file put it and still cannot be seen.
  IF THE 13.4 MM IS REAL the fix is a gap in the channel slab at the gully or the
  grate rising to the surface, and that is a street-spec change with its own review.
