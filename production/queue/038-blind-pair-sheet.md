line: infrastructure (D1 comparison, the blind reading)
spec: game-design/decision-2026-09-02-tiebreak-reversed-and-the-moat-item.md, Ruling 2
acceptance: tools/blind-pairs.py composites each of the four pairs with sides assigned by a seeded coin, writes the map to production/d1-probe/blind/map.json and the unlabelled sheets beside it, refuses to run if any of the eight stills is missing (printing which), and a sheet file with A, B or EQUAL per pair must be committed before a second invocation will print the map; selftest accepting case first on planted images, rejecting case a missing still
max_sessions: 1
status: WAITS 2026-09-02 until UE Phase B lands a still. instrument-builder. Both engines commit engine-named files today, so no blind look is possible without this.

WHY THIS EXISTS NOW RATHER THAN LATER. Jafar reversed the tie-break to
Unreal on 2 September. A stated preference for one engine and a blind
reading of the pairs can both hold, and they coexist BY ORDER: write A, B
or EQUAL for each pair on the D8 decomposition, and why, BEFORE any label
is unmasked; the tie-break is applied to that written sheet afterwards by
whoever unmasks it.

That is only true if the sheet can actually be blind. Today it cannot:
both engines commit files named after themselves, so anyone opening a pair
knows which is which before forming a view. The preference would then be in
the sheet as well as in the rule, and the comparison would be measuring
the reader.
