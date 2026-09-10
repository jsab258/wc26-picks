line: infrastructure (the guards)
spec: caused by the resident 2026-09-05, noticed before it did harm
acceptance: a second verify started while one is running either refuses with the running one named, or writes to its own file and the reader is told which run it is reading; proven by starting two deliberately, accepting case first (one run alone still writes the footer normally)
max_sessions: 1
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-05. NOT STARTED THIS WEEK by Jafar's rule that after item 4 the studio stops building studio. instrument-builder, small.

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


## FOURTH FIRING, 2026-09-06, AND THE RESIDENT'S READING OF IT WAS WRONG

The section that stood here claimed two reds were false and that nothing was
wrong with the bot. BOTH REDS WERE TRUE. What follows is the corrected
account, kept in place of the wrong one because the misreading is the useful
part.

What happened. Two agents were live and the systems-builder was editing
`ledger/verify.py`. The engine-specialist ran verify to check its own work and
reported two reds it had not caused:

    BOT CONFIG SELFTEST RED (tools/runner/telegram-bot.py)
    OUTBOX SELFTEST DID NOT REPORT

The resident tested the first by running
`python3 tools/runner/telegram-bot.py --selftest | tail -5`, read
`botconfig selftest: 12 passed, 0 failed`, and declared the red false.

THAT TOOL PRINTS TWO COUNT LINES. The one that governs,
`telegram-bot selftest: 70 passed, 3 failed (73 case(s) run)`, sat twelve
lines above the one the tail showed, and `verify.py` reads the FIRST match.
The resident checked a different question from the one the gate asks and
reported the answer as though it were the same question. Tailing a tool that
prints more than one verdict is the same error as reading a peak for a median,
and it was made within the hour of writing a queue item about reading the
wrong number out of a footer.

Both faults were real and they had ONE root cause, found by the builder sent
to fix them: a fixture pinned to a wall clock. producer-check's GOOD sample
states `DEADLINE 2026-09-07.`, and the send-time check is wall-clock BY
RULING, so the reading decayed through the floor at 09:00 that morning:

    pinned to the 2026-09-05 in its own filename   57.0 h
    --now 2026-09-06T09:00                         24.0 h, exit 0, the instant it crossed
    09:24, the director's run                      23.6 h
    09:41                                          23.3 h

About 0.1 h lost every six minutes and never recovering. The outbox crash was
downstream of the same decay: the good file was refused, so no receipt was
written, so `rec` was None and the comparison raised.

ONE DECAYED FIXTURE READ AS THREE FAULTS IN THREE DIFFERENT RULES, because two
of the three failing cases asserted against a CUMULATIVE send counter that only
reached 1 when the accepting case sent. Their own subjects, the word cap and
the register-in-the-name rule, were entirely healthy.

## What this leaves for queue 110 proper

The concurrency worry that opened this section still stands and is unproven
either way: a `verify.py` being written while it is read is a real hazard and
this run could not distinguish it from the decay, because the decay alone
explains every red observed. So this firing is NOT evidence for the
concurrency fault. It is evidence for two other things, and both are now
fixed in the tools: a selftest that dies must still print its count line
(exit 4 now means the suite itself raised, distinct from exit 3, a case
failed), and a tool that prints more than one verdict must end with the
whole-run one.
