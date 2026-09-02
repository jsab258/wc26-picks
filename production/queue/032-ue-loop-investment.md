line: infrastructure (D1 probe)
spec: game-design/decision-2026-09-02-d1-timebox-retired.md, Ruling 5
acceptance: the round trip's cost measured before anything is built to reduce it; then one named change, with the before and after times printed
max_sessions: 2
status: READY 2026-09-02. Numbered 032 because 031 was taken by a different finding written the same hour. RISES 2026-09-02 (game-design/decision-2026-09-02-tiebreak-reversed-and-the-moat-item.md, Ruling 1): with ties to Unreal, (a) decides D1 and this item's printer is (a)'s instrument. Step one rides 027's first UE dispatch; the named change waits for the printed series.

Jafar removed the engine deadline and said to spend the time on getting
Unreal working. MORE TIME THROUGH THE SAME LOOP IS NOT THE SAME THING AS
MORE PROGRESS. The loop is: write C++ blind with no compiler in this
container, dispatch, wait about twenty minutes, read whether it compiled.
Removing the deadline does not make that faster; it just buys more turns of
it.

So the first response to "more time" is a CHEAPER LOOP, not more attempts
through the expensive one.

MEASURE FIRST. Nothing today records what a UE round trip actually costs,
broken into its parts: queue wait, build, cook, package, run, commit. Print
that series before choosing what to fix. A guess about which part dominates
is exactly the guess this project has a rule against.

Candidate shapes, none built, none ruled:

1. A COMPILE-ONLY LANE. A dispatch that builds and stops, with the error
   patterns pulled from a real failing log rather than invented. If most
   failures are compile errors, this converts a twenty-minute answer into a
   much shorter one. The director's note: the cook step's existing pattern
   list is the STARTING POINT for those patterns, not the answer.
2. Anything that lets a signature be checked without a dispatch.

The cost that dominates is unknown until step one runs. Do not skip it.
