# Verification: instruments, judges, gates

Instruments (carried): CI builds, Core test suite, screenshot pipeline, frame and memory budgets, latency captures, gossip propagation checks, save chaos runs, headless mission playthroughs, repetition blind tests.

Judges (new, per D7): calibration sample 30 to 50 items graded by Jafar; deploy at 80 percent or better held-out agreement with zero false passes on canon violations; 10 percent ongoing audit; recalibration triggers as in D7.

Standing gates, run in CI or pre-integration:
1. Canon gate: era, names, tone, register. Mechanical checks where possible (banned terms: mobiles, internet, real brands; date windows), judge checks for tone.
2. License gate: every asset and generated output carries a license tag from the allowlist; untagged means failed.
3. Doc-decay gate: roadmap rows over 80 words, or verified-date older than 14 days against code changes touching the same area, fail.
4. Perf gate: frame and memory budgets per phase; regressions block integration.
5. Latency gate: live conversation budgets (first token, first audio) once Phase 2 lands.

Playtesting: Claude-driven bots do the volume (headless plus scripted runs plus vision checks on captures); Jafar does feel checks at phase gates and audits judge samples. Bug triage is clustered and summarized before it reaches a human.
