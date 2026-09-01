# Verification: instruments, judges, gates

Instruments (carried): CI builds, Core test suite, screenshot pipeline, frame and memory budgets, latency captures, gossip propagation checks, save chaos runs, headless mission playthroughs, repetition blind tests.

CALIBRATION SAMPLE SHAPE (learned 2026-08-31, lesson L4): a sample MUST
span the decision boundary. An all-PASS sample is not a calibration set,
because a judge that returns PASS to every input scores 100 percent
agreement against it; and D7's zero-false-passes clause is unmeasurable
unless the sample CONTAINS canon violations by construction. Build every
sample in three bands: clean and in register, canon-clean but register
wrong, and deliberate canon violations. Keep the objective key (which items
violate canon) in a separate file so the human's grading is uncontaminated.
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
