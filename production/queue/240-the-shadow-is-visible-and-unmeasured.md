line: instruments
spec: The shadow probe classifies against the sun the run ACTUALLY used, so a
  cast shadow that is plainly in the picture is not reported as lit ground.
acceptance: on ue-vign_pin_030_afterday, a shadowed asphalt population with a
  non-zero count and its own mean, beside the lit one, and the step between them
max_sessions: 1
status: READY 2026-09-10 14:10Z. THE EYE AND THE INSTRUMENT DISAGREE AND THE EYE
  IS PROBABLY RIGHT, which is the shape rule 3 says to resolve by suspecting the
  instrument first.

  WHAT THE PICTURE SHOWS. Run 41's pinned frames at 0.30 and 3.00 carry a clear
  diagonal shadow across the carriageway, cast by the left-hand building. It is
  the first time a cast shadow has been visible in this street, and it follows
  the sun repair (36 degrees where it had been rendering at 82) plus a pinned
  exposure that stops the frame washing out.

  WHAT THE INSTRUMENT SAYS. tools/frame-shadow-probe.py on that frame reports
  surf.asphalt=lit/n29141/mean0.6817 and NO SHADOWED POPULATION AT ALL, so it
  prints no step. Its own three checks pass and pass well: lumaCrossCheck
  mine/0.6590 against engine/0.6590, quadReproject 3/3, skyline median 0.0 px
  over 1280 of 1280 columns. THE RULER IS GOOD AND THE CLASSIFICATION IS NOT.

  THE LIKELY CAUSE, NAMED AS A HYPOTHESIS AND NOT A FINDING: the probe decides
  which sampled points are shadowed by predicting the sun's occlusion, and the
  sun MOVED 46 degrees when the elevation bug was repaired. A predictor built
  when the light came from almost overhead will place the shadow somewhere the
  shadow no longer is. Check that before changing anything.

  AND MY OWN FALLBACK MEASUREMENT CANNOT SETTLE IT, which is why this is a queue
  item and not a fix. Splitting band.ground by luma gives two populations at
  every pin, but that band spans road, kerb AND pavement, so the split separates
  MATERIALS and not lit from shadowed. A number that cannot tell a kerb from a
  shadow is not evidence of a shadow.

  ONE THING NOT TO CONCLUDE FROM THE PIN LADDER. The ground ratio reads 1.80 at
  pin 0.30, 4.50 at pin 3.00 and 2.08 unpinned, so THE RATIO MOVES WITH THE
  EXPOSURE. That is the review's own ruling in evidence: a ratio is monotone
  under this tonemapper and not linear, so it is robust and not invariant, and
  our ratio may not be compared with the reference sheet's 3.65 across different
  exposures. Pin 3.00's 4.50 also sits on a p05 of 0.0569, a denominator
  approaching zero, which is the instability queue 221 already names.
