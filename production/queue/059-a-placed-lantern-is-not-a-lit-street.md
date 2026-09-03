line: production (D1 admissibility, the Unreal side)
spec: this file, from run 17's four frames opened 2026-09-03
acceptance: (1) a per-light contribution reading on the scene line that answers "did this light reach the frame", not merely "was it placed": for each lantern and practical, the luma of the frame with it on minus the same frame with it off, at a named sample region, printed as a series before any bound is set; (2) an exposure reading per shot naming what the tone mapper did, with the clipped-pixel count at both ends over its denominator (shotPixels), so a blown ground and a crushed night are numbers rather than impressions; (3) both fixtures run in the ue-probe selftest against committed frames, accepting case first
max_sessions: 1
status: READY 2026-09-03. engine-specialist. Found by opening run 17's four frames, which is the only way it could have been found.

## The finding

Run 17 rendered the street in Unreal for the first time. The scene line is
clean and every word of it is true:

    lanternsPlaced=4/4 windowsLit=3/3 piecesEmitted=593/593 sceneStatus=WHOLE

And the two night frames are almost black. `vign_camB_night` measures
`shotMaxLuma=0.0993` and `shotDistinctBuckets=19/32768`: nineteen distinct
colours in a 1280x720 image. `vign_camA_night` is a bright sky behind
buildings that are pure silhouette. Four lanterns are placed in the street
and NOTHING IN EITHER FRAME IS LIT BY THEM. What light there is comes from
the ambient trilight.

THE INSTRUMENT IS NOT LYING AND THAT IS THE POINT. `lanternsPlaced=4/4`
answers "were four lantern lights created". It was never asked "did any of
them reach a pixel", and those are different questions with the same word in
front of them. A reader greps the scene line, sees 4 of 4, and concludes the
street is lit. The frame says otherwise and only a person opening the frame
can know.

The same gap at the other end of the range. Both day frames blow out:
`shotMaxLuma=0.9965` and `0.9804`, and the road and pavement read as flat
white with no tone in them at all. `shotMeanLuma` is 0.50 and 0.57, which is
a perfectly healthy-looking pair of numbers for an image whose entire ground
plane is clipped. A mean cannot see clipping; that is what a mean is for.

## Why this is the whole D1 comparison and not a polish item

D1 judges Unreal against Unity on four pairs, blind, on the D8 decomposition.
A night pair where one engine's lanterns light the street and the other's do
not is not a judgement about renderers, it is a judgement about whether
somebody wired the lights. An exposure difference is the same fault wearing
brighter clothes. Both would be scored as visual quality and neither is.

So this is admissibility, not looks: until a light's CONTRIBUTION and a
frame's CLIPPING are measured, a judged pair can be decided by a bug and the
sheet will not show it.

## The shape of the numbers, because two of them are traps

A per-light contribution is a DIFFERENCE and needs its two halves named: the
same camera, same condition, same frame count, one light toggled, and the
sample region stated, because a lantern that lights the far end of the street
contributes nothing to a crop of the near end and that is not a failure.

Clipping ships as a COUNT WITH ITS DENOMINATOR at both ends, never as a mean.
`shotMeanLuma=0.5030` and a fully clipped ground plane are the same reading,
which is exactly rule 3b's shape: a healthy summary statistic over a
population that is not healthy.

No bound in this item. Ship the printers, read run 18 and 19, set the numbers
from the series after (rule 2).

## Not in scope

Do not fix the exposure or the lamp gain in the same session. `lampGain=1.00`
and `fogGain=1.00` are first values with no series behind them and they stay
that way until something prints one. Measure first.
