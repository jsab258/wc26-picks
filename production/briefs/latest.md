# LEDGER weekly brief, 2026-08-31 (the first under v2)

## Landed
1. The v2 respec package, committed verbatim after integrity checks; it now
   governs. canon.md written, amended per your rulings, APPROVED; the two
   conflict resolutions are decision records D8 (visual bar: Meridian Test,
   GTA V PS3 retired, M17.10 decomposition kept as technique) and D9
   (quality ceiling: Meridian Test, AA/premium indie dropped).
2. Repo migration: old roadmap, design doc and visual-bar spec preserved
   whole in legacy/ under SUPERSEDED headers; CLAUDE.md points at the
   package; the license allowlist and formatting law are stated as binding.
3. Phase 0 scaffold: production/ (queue state machine, token ledger,
   throughput ledger, briefs, per-agent scratch), the overnight runner
   (dispatch prompt, loop script, one-click bat, kill switch, fallback
   brief), three v2 agent roles with standing constraints baked in
   (planner, integrator, dialogue-writer), the mechanical canon gate and
   the dialogue verifier, both selftested on both outcomes.
4. The pilot assembly line ran end to end: spec, author, verify, integrate,
   record. content/dialogue/pub-regular-v1.json, 48 memory-conditioned
   lines across three ladder rungs and three contexts. Mechanical gates
   clean: canon, rung discipline, repetition (worst overlap 0.18 of a 0.6
   bound over 1,128 pairs), license tagged. First row in the throughput
   ledger.

## In flight
1. D1 engine probe, two-week box ending 2026-09-14, REORDERED: the Unity
   half runs first (queue 002 cycle baseline, 003 instrument inventory,
   004 the street to the Unity ceiling). None of it needs UE5.

## Blocked
1. Nothing. Both blockers cleared 2026-09-01: UE 5.8.2 is installing (the
   launcher fault was a known bug with a thirty-second workaround, not the
   account state I first diagnosed), and dialogue tone verification no
   longer needs Jafar at all.

## Numbers
1. Throughput: 1 verified piece this week (the pilot bank).
2. Judge agreement: nothing-measured, no calibrated judge yet.
3. Token spend: this session only, interactive, top model (the ledger
   opens this week; the routing law applies from the first runner night).

## Decision queue (yours, per operations.md)
1. CARD: the UE5 blocker, now with a researched fix rather than a
   question. This is a known Epic launcher bug: the launcher sits in an
   offline or empty-entitlement state and greys out every install control.
   Two documented workarounds, both about 30 seconds, either one likely
   enough that it is worth trying before any support ticket. They are in
   the reply and in the blocked task. If neither works, the fallback is an
   Epic support ticket with the symptom list already written.
   Recommendation: try them once; do not spend a second evening on it.
   Tasks 002 to 004 bank the Unity measurements regardless.
2. CLOSED: the calibration sample, graded 48 PASS. No further grading is
   asked of you for this content type.

## Next
1. A UE workflow mirroring the Unity one (queue 005), dispatched to the CI
   build agent already running on the PC. That is how the UE half of D1
   gets measured, and it asks nothing of Jafar. My earlier claim that the
   night loop was the critical path was wrong: two different things were
   both called "the runner" and the build agent has been doing machine-side
   work since 22 Aug.
2. D1 measurement c: DONE. Half the tool surface would be rebuilt on a move
   to C++; the obvious count flatters the move because the coupling is to
   the language, not the engine.
3. The night loop remains wanted for continuous autonomous development
   against the queue, which is a different job from the probe. It is no
   longer blocking anything.
