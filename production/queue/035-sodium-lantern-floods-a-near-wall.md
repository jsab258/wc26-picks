line: production (visual)
spec: production/specs/vignette-scene.json, the lighting block
acceptance: a printed series of lantern intensity and range against a measured wall luminance, then a bound chosen from it; cam_B night stops reading as a flood and cam_A night keeps its pooling
max_sessions: 1
status: WAITS 2026-09-02 behind 027 Phase B (game-design/decision-2026-09-02-tiebreak-reversed-and-the-moat-item.md, Ruling 4). Found by opening all four stills, which is the only way it could have been found. The lantern values live in the shared JSON, so both engines render the same flood and the pair stays fair; the first UE night frame says whether the flood is the JSON or Unity's light-unit conversion, and that is worth knowing before the printer is written.

THE TWO NIGHT FRAMES DISAGREE AND THE DIFFERENCE IS THE FINDING.

`vign_camA_night.jpg` is the best frame the project has produced: sodium
light pooling on wet tarmac with a real reflection streak down the road, a
black sky, brick catching the light at a grazing angle. That reads as a wet
British street at night.

`vign_camB_night.jpg`, the same lights and the same scene, floods. The
parade wall is square-on and close, and it comes back saturated yellow from
sill to roofline with no falloff. Real sodium lighting POOLS; it does not
wash a whole elevation evenly.

WHY THIS IS A MEASUREMENT AND NOT A TASTE NOTE. The lantern `range_m` and
`intensity` in the scene JSON are FIRST VALUES with no printed series, and
the builder labelled them as such in the file rather than presenting them as
chosen. So this is the unmeasured guess showing itself at the first camera
angle that could reveal it, exactly as an unmeasured number should.

Ship the printer before touching the number: wall luminance at a named
sample point against lantern intensity and range, across the values, printed
as a series. Then set the bound from what it prints. Do not tune by eye
first and measure afterwards, which inverts the rule this project keeps.

The camera is not the variable. Two angles on one lighting rig disagreeing
is the rig, and a per-camera fix would be tuning the instrument to the
reading.
