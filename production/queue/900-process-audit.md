line: verification (weekly process audit; CHEAP MODEL per the routing law)
spec: ledger-v2/studio-v2/learning.md and this file
acceptance: every check below reports a number or a named violation; violations become queue items; findings summarized for the morning brief
max_sessions: 1

Run weekly. On completion, re-enqueue yourself dated next week (copy this
file to 900-process-audit.md with the completed one moved to done/ carrying
the findings), so the audit is standing without a scheduler.

Checks, each with its denominator:
1. Roadmap row caps: every row in ledger-v2/respec/roadmap-v2.md under 80
   words; count rows checked.
2. Token ledger currency: production/token-ledger.md has a row for the
   current week; escalations recorded with reasons.
3. Single-deliverable briefs: sample the week's done/ tasks; any task that
   shipped two deliverables is a violation (waste lesson 3).
4. Namespaced scratch: production/scratch/ contains only per-agent dirs; a
   shared file at its root is a violation (waste lesson 4).
5. Lesson termination: every blocked/ item, audit finding and retrospective
   finding from the past week appears in learning.md's index terminated one
   of the four ways; list any unterminated as violations.
6. Harvest coverage: every phase marked closed since the last audit has a
   matching harvest commit on game-studio main (D10); a closed phase
   without one is a violation.
