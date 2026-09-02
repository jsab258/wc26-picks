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
7. Goal block verbatim: the goal block at the top of CLAUDE.md matches
   ledger-v2/respec/vision-pillars-v2.md word for word. Run
   `python3 tools/goal-block-check.py`; a non-zero exit is a violation.
   THE SOURCE WINS in any mismatch, because the copy is a copy: fix
   vision-pillars-v2.md if the goal itself changed, then re-copy.
   Jafar's instruction, 2026-09-01. It is a tool rather than a reading
   because comparing a paragraph inside a 15,000 word file against another
   file by eye, once a week, is exactly the check this project has watched
   decay before.
8. DANGLING CITATIONS: every decision number cited in any document
   resolves to a file in ledger-v2/respec/decision-register/. Collect every
   `D<n>` mention across the tree, map it to the register's files, and print
   BOTH counts plus every citation that resolves to nothing. Added
   2026-09-02 after D12 shipped citing a D11 that did not exist and denying
   a D10 that did. A dangling citation reads as authority: the number looks
   like a decision was made, and nobody checks.

9. CITATIONS CARRY NUMBER PLUS SLUG. A cross-reference is written
   `D10-framework-freeze`, never a bare `D10`. Renumbering a register entry
   then breaks the citation loudly instead of silently re-pointing it at
   whatever now holds that number, which is the failure mode a bare number
   cannot distinguish from being correct. Audit samples the week's new
   documents for bare numbers.

10. Status dashboard currency: STATUS.md carries the timestamp it was
   generated at, on line 3. It must be less than a day old at audit time,
   and the check reports the age it found rather than a yes or no. A page
   older than that is not a small untidiness: it is a page a reader will
   still read as current, which is worse than no page.
11. The dashboard writes nothing else: run
   `python3 tools/dashboard/build-dashboard.py --selftest`. Its AST walk
   asserts that every filesystem write in the generator is either
   write_artifact (which refuses any name but the two artifacts) or the
   selftest's own temp fixture, and its scope test asserts that a whole
   generation creates exactly two files and leaves the tree it read
   untouched. Report the passed and failed counts, both numbers, always.
   A derived page that quietly repairs a source it read is a second source
   of truth, which is the one thing it must never become.
