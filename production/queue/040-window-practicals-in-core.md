line: production (D1 comparison, admissibility)
spec: game-design/decision-2026-09-02-free-lane-and-piece-list-batch.md, Ruling 4
acceptance: Core reads lighting.window_practicals (lit_bays, shop and flat intensity and range, and a colour ADDED to the JSON as the Host's current value with its colour space named) into the Plan; StreetVignettePieces.Write emits a window_practicals block beside lantern and the drift guard is regenerated; StreetVignetteHost reads every value from the Plan, lights ONLY the listed bays, and prints `windowsLit=N/M` on the sim verdict with M the interior cards; the flat values, which light nothing today (D8_upper_windows carry no interior card), print `flatsLit=0/0 nothing-to-light` rather than vanish; CoreTests asserts 3 of 6 from the plan and the same after the round trip; one Unity dispatch shows three lit bays
max_sessions: 1
status: READY 2026-09-02. engine-specialist. Rides the 027 Phase A close-out session with A2 and 041, BEFORE Phase B.

FACTS INLINE. production/specs/vignette-scene.json 268 to 276 carries
lit_bays [0, 2, 5], shop_intensity 1.6, shop_range_m 7.0, flat_intensity
0.8, flat_range_m 5.0 and no colour. Nothing in ledger/Assets/Scripts reads
any of it (grep shop_intensity|lit_bays: 0 hits). StreetVignette.cs 1318 to
1319 is the lantern's read and the pattern; Plan fields at 197.
StreetVignetteHost.cs 259 to 272 lights every `_interior` piece (six in
production/specs/vignette-pieces.json) with Color(1, 0.86, 0.62), range 7,
intensity 1.6, shadows off. The pieces file's lantern block (line 13) is
the pattern for the new block. NAMED CONSEQUENCE: the Unity night frame
loses three lit windows; if that is worse, the value moves in the JSON for
both engines and never in a Host constant.
