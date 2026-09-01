# D10: game-studio frozen; one operative framework; harvest, not sync
Date: 2026-08-31. Status: APPROVED (Jafar, governance instruction). Owner:
Direction.
Numbering note: Jafar's instruction said "record decision D8", but D8 and D9
were assigned hours earlier at canon approval (visual bar; quality ceiling),
on his own ruling to record both conflict resolutions. The freeze is
therefore D10, and the discrepancy is named here rather than silently
renumbered.
Context: two repos both claimed to carry the framework. game-studio (the
Measured Studio template) was extracted from LEDGER v1 and kept in step by a
continuous-sync gate that went red whenever CLAUDE.md's process sections
changed. Under v2 the operative framework moved into ledger-v2/studio-v2/ in
this repo, so continuous sync would mean maintaining the same rules in two
places, which is the two-implementations trap with a repository for a blast
radius.
Choice: game-studio is FROZEN as legacy reference. ledger-v2/studio-v2/ is
the single operative framework. No continuous sync between the repos.
game-studio is updated ONLY by harvest: a mandatory phase-exit step that
distills portable lessons into it as a clean rewrite (mechanics in
studio-v2/learning.md). A harvest can also be enqueued manually.
Consequences, all executed with this record: the template_sync verify gate is
retired in place with the reason in its body (learning.md lesson L1); the
freeze is marked in game-studio itself with a README status line reading
"framework distilled from LEDGER production, current through Phase R"; the
weekly process audit checks that every closed phase has a matching harvest
commit.
Instrument: the process audit (production/queue/900) and the phase-exit
checklist in studio-v2/operations.md; a closed phase with no harvest commit
in game-studio main is a failed audit.
Revisit when: a second game starts and wants a live framework repo; that is
a new decision record, not a quiet unfreeze.
