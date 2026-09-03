# `groundGainBy` — the geometry filter, and the ungraded twin

> **STATUS: LOG, 2026-08-25. NOT CURRENT** once landed.

Built by instrument-builder against the director's ruling at
`game-design/decision-ground-albedo.md` §C (landing 3a4e335). One dispatch,
two parts, in the order the ruling set: the filter conditions the tally, both
emits read the filtered tally. **Nothing committed.**

## What was wrong

`groundGainBy` landed once and its rows are not ground. `AssetLibrary
.GroundSurfaceOf` is a material-NAME match with no geometry, so the rows
carried building facades (`Concrete` is in the facade arrays at
`WorldBuilder.BuildBuildings` and `BuildDistrict`), the `mat_concrete_b`
facade variant folded on by `SurfaceNames`'s `_b` strip, odd-id vehicle paint
(`TrafficHost.PaintFor`, `v.Id % 2 == 0 ? Metal : Concrete`), and give-way
bars painted `Sidewalk` by `StreetFurniture`. `concrete` was 2673 of 6041
rays. Taken as established from the tier-2 verification; not re-derived here.

Second fault, and the one the A/B exists for: every frame-sampled number in
this fork is POST-GRADE. `groundGainBy`'s numerator is
`tonemap(exposure x light x albedo) + bloom + grain`; its denominator is a raw
material constant. Bloom is additive and albedo-blind, so the ratio explodes
as the denominator falls — which is the shape of `asphalt:68.121` against
`kerb:4.911` on 3a4e335, and it is quotable only as that signature.

## Part 1 — the normal filter

`SimDirector.GroundUpDot = 0.9f`, applied at the ray site where `hit` is in
hand, after the name match and after the `groundMask*` family has counted the
ray. A ray is admitted to the gain tally only when `hit.normal.y > 0.9`.

It is a GEOMETRIC CLASSIFIER, not a tuned bound, and the comment says so:
ground in this town is horizontal by construction (every road, pavement, kerb
top and yard is an axis-aligned box laid flat by `WorldBuilder`), so a ground
normal is (0,1,0) and a facade's is (+/-1,0,0) or (0,0,+/-1). There is no
population of surfaces between 25 degrees and vertical for the number to cut
through. It gets no series and no gate; it is audited by its own dropped count.

**It lives at the ray site, not in `GroundSurfaceOf`.** That function answers
"what is this material called". Its doc comment now says outright that it does
not answer "is this ground" and must never be made to, and names the ray site
as the place that supplies the geometry test.

**It guards `_groundGain` and nothing else.** `groundMaskMeanBy`,
`groundMaskThirdsBy`, `groundMaskOverFrameBy`, `groundMaskOverLowerBy` and
`groundMaskRays` are a landed series; narrowing what they count would be a
regime change no aggregate over their past readings could see, and this
dispatch was ordered to fix one key. The thirds accumulation MOVED UP the loop
body so it still sees every name-matched ray — the first draft repeated it in
the skip branch, which is one idea in two implementations.

## Part 2 — the `FilmGrade.Bypass` A/B

`GroundMaskRead` renders ONE extra frame per district shot, same camera, same
instant (`DistrictTour` takes no time step and nothing moves `cam`), at the
same resolution as the committed still, with `FilmGrade.Bypass = true`. The
rays are not re-cast: the loop raycasts once and reads both pixel arrays at the
same `row * w + col`.

Pattern copied from the file's own three Bypass sites (`MeasureNightLight`,
`ProbeFrameCost`, the facade ladder). `Bypass = false` is in a `finally` and
runs first in it — a static left set would silently ungrade every later still.

`postFrames` (`FilmGrade.Frames`) gains one per district shot, seven on a
seven-district run against a landed 25,876; `postOk` is `Frames > 0` and cannot
move. Named in the comment so nobody reads it as a regression.

## One filter, one ray set — structurally, not by adjacency

There is no second `GroundGain` object. One `Add` call takes both numerators:

    _groundGain.Add(logical, materialName, gradedLuma, sourceAlbedo, rawLuma, rawKnown)

and the class emits twice (`Emit` / `EmitRaw`). Two tallies fed by two adjacent
statements is the shape that gave this project four pairs of numbers taken at
different instants and printed as one event; with one entry point the graded
and raw rows cannot describe different rays however the ray site is later
edited. `groundGainRawRays=a/b` reading equal is the on-the-line proof.

`rawKnown` is false when the bypass render throws. The graded arm is then
untouched and the raw row prints `nothing_measured@0of<admitted>up` — a raw row
reading `0.0000` would be read as a scene that is black before the grade, which
is the exact conclusion the A/B exists to test.

## The keys

    groundGainBy=[<name>:<graded>/<source>=<ratio>@<n>up/<n>notup^<topMaterial>,...]
    groundGainOf=<rows with rays>/<surfaces offered>
    groundGainRays=<admitted>/<notup>/<mask's name-matched ground rays>

    groundGainByRaw=[<name>:<raw>/<source>=<ratio>@<n>of<n>up,...]
    groundGainRawOf=<rows with rays>/<surfaces offered>
    groundGainRawRays=<raw rays>/<admitted rays>
    groundGainRawShots=<shots with a raw twin>/<district shots offered>

`admitted + notup == mask ground rays` by construction. The raw arm prints no
`notup` and no `^`: those describe the ADMISSION, which is one decision shared
by both keys, and printing them twice would be one number under two names.

Statistics, named: `graded` / `raw` / `source` are RAY-WEIGHTED MEANS over the
admitted rays of the whole district tour (not peaks, not medians, not per
shot); `ratio` is a RATIO OF MEANS; `^` is a MODE over material names with
ordinal tie-break; `notup` is a cumulative count. Both numerators are LINEAR
(`Color.linear` at the ray), both denominators are `MatAlbedo`, already linear.
`groundMaskMeanBy` is the frame's sRGB and must not be divided into either.

## Selftest

`CoreTests.TestGroundGain`, accepting case first, exact strings. 3834 checks
pass. Rejecting fixtures are synthetic — `mat_nosuchsurface`, and a material
named `mat kerb, spaced=odd@1 (Instance)` — so doing the work the tool prompts
cannot break the tool.

## What is NOT measured yet

`kerb`'s collapse is a PREDICTION from geometry (`WorldBuilder` builds kerbs as
0.2m strips), not a reading. The Game layer does not compile in this container;
the live rows need the Windows build. The comment at the emit already says a
`0up` row is a finding about the OLD row and not a fault in the filter, so it
is in place before the number arrives.

`tools/verdict-keys.py --learn` will need running once the four new keys land.
