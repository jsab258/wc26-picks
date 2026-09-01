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
1. D1 engine probe, kicked off, two-week box ending 2026-09-14. Plan at
   production/d1-probe/plan.md; first two queue tasks written. The probe
   cannot start until UE5 is on the build PC, which is queue task 000 and
   yours.

## Blocked
1. Dialogue TONE verification: the judge needs your calibration sample
   before it can grade anything (D7). Until then tone is honestly marked
   PENDING, not passed.

## Numbers
1. Throughput: 1 verified piece this week (the pilot bank).
2. Judge agreement: nothing-measured, no calibrated judge yet.
3. Token spend: this session only, interactive, top model (the ledger
   opens this week; the routing law applies from the first runner night).

## Decision queue (yours, per operations.md)
1. CARD: install UE5 on the build PC (queue/000). Question: none, it is an
   action; about 40 GB disk, one click in the Epic launcher. Consequence
   if deferred: D1 measures Unity only and the probe becomes a formality.
2. CARD: grade the judge calibration sample,
   production/specs/judge-calibration-1-dialogue.md, 48 lines, PASS/FAIL
   plus a word per FAIL. Consequence if deferred: dialogue throughput has
   no tone gate and the assembly line runs mechanical-only.

## Next
1. Runner's first supervised night on the PC (one trivial task queued,
   watched, then -Register the schedule).
2. D1 week 1: perception core transliteration once UE5 exists.
3. Second assembly line spec (signage/brand bible) once the calibration
   sample is back.
