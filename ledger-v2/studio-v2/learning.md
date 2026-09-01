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
| L4 | 2026-08-31 | judge calibration sample 1 came back 48 PASS, 0 FAIL: a set with no rejecting case cannot separate a calibrated judge from one that always says PASS, and D7's zero-false-passes-on-canon clause was unmeasurable because the canon gate had already cleaned the bank | rule edit: a calibration sample MUST span the decision boundary and MUST contain canon violations by construction; sample 2 built to that shape | ledger-v2/studio-v2/verification.md; production/specs/judge-calibration-2-dialogue.md |
| L5 | 2026-08-31 | the judge's rejecting fixtures contain canon violations by construction, so the canon gate would refuse the fixture that makes the gate measurable | gate change: fixture path exempt by name, exemption printed when it bites, and a selftest proving the same text still refuses outside the fixture path | tools/canon-gate.py |
| L6 | 2026-09-01 | Jafar: "I don't want to be tested like I'm doing an exam at school, and from the beginning I said I want minimal manual work." A second grading sheet was built for him after sample 1 came back all PASS | rule edit: calibration and test set are separate artefacts with separate owners; the human grades only the positive boundary, the studio constructs and labels the negatives, and the ongoing audit is the check on that | ledger-v2/studio-v2/verification.md; production/specs/judge-test-set-1-dialogue.md |
| L7 | 2026-09-01 | six troubleshooting routes tried from reasoning produced a confident wrong diagnosis (Epic account entitlement); one search found a widely reported launcher bug and a thirty-second fix | explicit no-change note: no rule is added. "Search first" as a standing rule would be cargo cult, and the existing rule (suspect the instrument, check before asserting) already covers it. What is recorded is the discriminator: an account-state symptom and a UI-bug symptom are indistinguishable from the inside, so the cheap test is whether other people have seen it | production/queue/done/000-d1-ue5-install.md |
| L8 | 2026-09-01 | two different things were both called "the runner" (the CI build agent on the PC since 22 Aug, and the night loop written 31 Aug); I declared the night loop D1's critical path when the build agent had been doing machine-side work for ten days. Jafar caught it by asking what the .bat does | rule edit plus doc fix: tools/runner/README.md now opens by distinguishing them, and a task saying "the runner" without naming which is rejected at spec | tools/runner/README.md; production/d1-probe/plan.md |
| L3 | 2026-08-31 | tools/runner/README.md was written without checking the directory, which already housed the v1 build runner | no-change note: nothing was in fact overwritten (checked in git after the alarm); the README now names both tenants, and the standing rule "look before you write" already covers it | tools/runner/README.md |
