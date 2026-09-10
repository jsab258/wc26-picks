line: art (the authored street)
spec: Measure, then decide. The next walk run prints the drainage grate's placed
  world-bounds top against the channel surface height at x=12, and whether any piece
  occupies the 0.4 m by 0.4 m footprint above it.
acceptance: the burial is confirmed or refuted by a placed-bounds reading rather than
  by arithmetic on a spec file, and if confirmed the street spec changes under its own
  review
max_sessions: 1
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-08, and it BLOCKS THE CLAIM that a walk clip shows Jafar's item
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
  AMENDED IN PLACE 2026-09-09 BY AMENDMENT A13 of
  game-design/decision-2026-09-09-the-twelve-clauses-and-the-buried-grate.md, section
  3, after a builder built the instrument and a second director checked the arithmetic
  off the JSON. THE MAGNITUDE AND THE STATED FIX BOTH CHANGE.
  THE MAGNITUDE: 13.234 mm by the unpitched arithmetic, so the original 13.4 was a
  0.166 mm slip and not a misread row. Taking the 1.432096 degree cross-fall gives
  14.90 mm at the grate's centre line, and the cover runs 19.90 / 14.90 / 9.90 mm west
  to east across the footprint, so NO PART OF THE GRATE REACHES THE SURFACE.
  AND THE CHANNEL IS NOT THE DEEPEST COVER, which kills the fix this item first
  proposed. ground_east_carriageway straddles the grate's top over 36.2 percent of its
  footprint; the channel slab is 0.255 m wide against the grate's 0.3999 m; and the
  two slabs OVERLAP by 0.469 mm with no gap between them. The grate is under the road
  as well as under the channel, so cutting a gap in the channel slab would uncover
  nothing.
  THE FIX IS ONE ROW RISING AND TAKING THE CROSS-FALL: y_m from -0.0925 to -0.077502 and
  pitch_deg from 0 to 1.432096. A FLAT grate raised to be flush at its centre line
  leaves a 5 mm lip, which is why the pitch is part of the fix and not a refinement of
  it. It is a street-spec change and it lands under the art line's review.
  ONE FIGURE IS STILL UNSETTLED AND A8 SETTLES IT: 18.7 mm could not be reproduced;
  the plane gives 19.90 mm at the footprint edge and 18.7 sits about 48 mm inside it.
  The per-cell depth series is what decides between them.
  AND THE ACCEPTANCE MAY NOT BE READ OFF propBurialWorst. After a perfect fix the same
  subject still prints about 36 percent at 65.11 mm, because that key is an AABB
  reading against a pitched slab. Read the per-cell series or a placed-bounds reading,
  never the headline.
  THE PRESCRIBED y WAS 0.1006 mm LOW AND THE EMITTER CORRECTED IT. The ruling
  prescribed y_m -0.0776; the regenerated row reads -0.077502, and the emitter
  derives it from the scene file's own crossfall and dish_depth_m rather than
  from a typed number, which is why an arithmetic disagreement was possible at
  all.
  THE CAUSE, DECOMPOSED 2026-09-09 AND NOT ONE THING. An earlier note here
  credited the whole gap to a slope written as 0.025005 against the slabs' own
  0.025. That is 7 percent of it. The other 93 percent is a different mistake:
  the prescribing plane anchored a TILTED slab's top-face height at the piece's
  own z, when going up the normal also moves that face 3.7488 mm in z, which
  costs 0.15 x sin(1.432096 deg) x 0.025 = 0.0937 mm. The tan slip costs
  0.0072 mm over 1.4312 m. Together 0.1009 against 0.1006 observed, residual
  0.3 um, which is the file's own six-decimal rounding.
  SO IT IS UNDERSTOOD RATHER THAN RECURRING. ue-probe/Source/LedgerProbe/Public/
  VignetteSpec.h already carried the 93 percent half correctly ("the pitch shifts
  that face 3.75 mm in z, which is 0.09 mm of y") while this file carried only
  the 7 percent half, so the project held two records of one cause and quoted the
  wrong one. Only this instance is claimed; the two earlier disagreements this
  note once swept in are not re-derived here and are not claimed.
  THE 75 MICROMETRE OVERHANG IS ACCEPTED AND NAMED so it is not rediscovered as
  a bug. Pitching the grate shifts its top face 187 um in +z, which puts the east
  corner 75 um past the kerb face and therefore 75 um inside the gully kerb block.
  It is six times smaller than the 0.469 mm slab-to-slab overlap this street
  already carries and it is invisible; it is also the entire source of the
  65.01 mm row in the per-cell series, which is why it is written down.
  ALL OF THE ABOVE IS SPEC-LEVEL. propsAsMesh=0/23, so no placed reading of this grate
  has ever existed.
