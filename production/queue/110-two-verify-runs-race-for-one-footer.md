line: infrastructure (the guards)
spec: caused by the resident 2026-09-05, noticed before it did harm
acceptance: a second verify started while one is running either refuses with the running one named, or writes to its own file and the reader is told which run it is reading; proven by starting two deliberately, accepting case first (one run alone still writes the footer normally)
max_sessions: 1
status: READY 2026-09-05. NOT STARTED THIS WEEK by Jafar's rule that after item 4 the studio stops building studio. instrument-builder, small.

## What happened

The resident started `ledger/verify.py` in the background, made corrections to
the tree, then started a SECOND run before the first had finished. Both write
`ledger/.verify-footer`. Two were live at once, measured:

    still running, pid 1709
    still running, pid 5665

The older run was measuring the tree BEFORE the corrections; the newer one
after. Whichever finished last would own the file. Had the older won, the
footer would have described a tree that no longer existed, and the commit
message would have carried it as evidence.

Caught only because the footer's timestamp read 17:35 when the corrections
were made at about 20:50, and the resident checked the clock rather than the
colour. The older run was killed by hand.

## Why this is the project's own recurring shape

An instrument that quietly describes a DIFFERENT MOMENT than the one the
reader thinks they are reading. The footer carries no run identity: nothing in
it says which invocation produced it, so a reader cannot tell a fresh footer
from a stale one except by comparing a file timestamp against a memory of when
they last changed something. That is not a check, it is a habit, and habits
fail at exactly the moment a session is busy.

## Two honest routes

1. REFUSE THE SECOND RUN. A lock file naming the running pid and its start
   instant; a second invocation exits saying which run holds it and since
   when. Simple, and it makes the failure impossible rather than visible.
2. GIVE THE FOOTER ITS RUN IDENTITY. Each run writes its own pid and start
   instant into the footer, and the commit path refuses a footer whose start
   instant is older than the newest modification to any file it describes.
   Harder, and it fixes the general case rather than this instance.

Route 1 is the smaller change and closes the observed fault. Route 2 also
closes the case where ONE run is simply stale because the tree moved under it,
which is the same fault without a second process, and which the current
`verify-gate.sh` catches only for tracked files it walks.

## Both halves

Accepting: one run alone behaves exactly as it does today and writes the
footer.
Rejecting: two runs started deliberately, and the second refuses or is
distinguishable, with the message naming the other run. A fix that silently
serialises them has hidden the collision rather than reported it.
