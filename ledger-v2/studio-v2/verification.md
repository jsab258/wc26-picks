# Verification: instruments, judges, gates

Instruments (carried): CI builds, Core test suite, screenshot pipeline, frame and memory budgets, latency captures, gossip propagation checks, save chaos runs, headless mission playthroughs, repetition blind tests.

TWO ARTEFACTS, TWO JOBS, AND ONLY ONE OF THEM COSTS A HUMAN (learned
2026-09-01, lessons L4 and L6).

A CALIBRATION SAMPLE is graded by the human and fixes the POSITIVE
boundary: this is the register, in his judgement. It is the only part that
needs him, it is done once per content type, and it must be short.

A TEST SET is CONSTRUCTED and labelled by the studio, never graded by the
human, because nobody should be asked to grade items built to be wrong. It
supplies the half a calibration sample structurally cannot: proof that the
judge REFUSES. Three bands: clean and in register, canon-clean but register
wrong, deliberate canon violations.

A judge ships only when it passes BOTH: agreement with the human's graded
sample, and zero false passes on the test set's canon band (D7).

Why the split rather than one big graded sheet: an all-PASS calibration
cannot separate a calibrated judge from one that always says PASS, so the
first instinct is to send the human more sheets including deliberate
rubbish. That is an exam, it is slow, and it spends the scarcest resource
in the studio on labelling items whose labels are already known. Construct
the negatives instead, and spend the human only on the positive boundary
and the ongoing 10 percent audit.

WHAT THE SPLIT COSTS, stated so it is not discovered later: the register
band's labels are the studio's reading, anchored on the human's approved
positives rather than measured against his negatives. The audit is the
instrument that catches that being wrong; audit disagreement above 20
percent makes those labels the first suspect, before the judge.

The violating items are rejecting fixtures and must be exempt from the
canon gate by path, with the exemption printed and a selftest proving the
same text still refuses elsewhere.

Judges (new, per D7): calibration sample 30 to 50 items graded by Jafar; deploy at 80 percent or better held-out agreement with zero false passes on canon violations; 10 percent ongoing audit; recalibration triggers as in D7.

Standing gates, run in CI or pre-integration:
1. Canon gate: era, names, tone, register. Mechanical checks where possible (banned terms: mobiles, internet, real brands; date windows), judge checks for tone.
2. License gate: every asset and generated output carries a license tag from the allowlist; untagged means failed.
3. Doc-decay gate: roadmap rows over 80 words, or verified-date older than 14 days against code changes touching the same area, fail.
4. Perf gate: frame and memory budgets per phase; regressions block integration.
5. Latency gate: live conversation budgets (first token, first audio) once Phase 2 lands.

Playtesting: Claude-driven bots do the volume (headless plus scripted runs plus vision checks on captures); Jafar does feel checks at phase gates and audits judge samples. Bug triage is clustered and summarized before it reaches a human.
