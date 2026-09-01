# Learning: the lessons pipeline (created 2026-08-31, Jafar's governance instruction)

This file holds ONLY the pipeline rules and the index of terminated lessons.
The lessons themselves live where they took effect: the amended rule, the
changed gate, the decision record. Agents inherit every lesson automatically
by reading the framework they already boot from; nobody re-reads a lessons
archive, because an archive nobody must read is an archive nobody reads.

## The pipeline
1. Sources: every production/queue/blocked/ item, every audit finding, every
   postmortem, every phase-exit retrospective finding.
2. Every source item MUST terminate in exactly one of:
   a. a rule edit in studio-v2/
   b. a gate change (a verify check, a lint, a pipeline station)
   c. a decision record in respec/decision-register/
   d. an explicit no-change note stating why nothing changes
3. The termination links back to the source, and the source links forward to
   the termination. An unterminated lesson from the past week FAILS the
   weekly process audit (production/queue/900).
4. The index below records each terminated lesson in one line with links.
   The index is also the HARVEST INPUT LIST.

## Harvest (mandatory phase-exit step; a phase cannot close without it)
1. Pull jsab258/game-studio as a sibling working directory.
2. From this index, take the lessons terminated since the last harvest and
   apply only those passing the PORTABILITY TEST: would this change apply
   unchanged to the next game? Portable: rules, gates, pipelines, the
   runner, the judge protocol, templates, waste lessons. Never portable:
   canon, era, cast, assets, tuned numbers.
3. REWRITE files rather than append, so game-studio always reads as a clean
   current framework, not a changelog.
4. Commit to game-studio main naming the phase and the source lessons.
   Summarize the diff in the morning brief.
5. Maintain the game-studio README status line: "framework distilled from
   LEDGER production, current through Phase N".
6. A harvest can also be enqueued manually at any time; the phase-exit one
   is the floor, not the ceiling.

## Index of terminated lessons
| id | date | source | terminated as | where |
|---|---|---|---|---|
| L1 | 2026-08-31 | D10 forbids the continuous-sync mechanism the template_sync gate WAS | gate change: template_sync retired in place | ledger/verify.py template_sync(); ledger-v2/respec/decision-register/D10-framework-freeze.md |
| L2 | 2026-08-31 | canon-gate refused the word "debts" (substring 'bt ' for a real brand) in a game about a book of uncollectable debts | gate change: brand matching word-bounded, both outcomes in the selftest | tools/canon-gate.py |
| L3 | 2026-08-31 | tools/runner/README.md was written without checking the directory, which already housed the v1 build runner | no-change note: nothing was in fact overwritten (checked in git after the alarm); the README now names both tenants, and the standing rule "look before you write" already covers it | tools/runner/README.md |
