line: infrastructure (the evidence channel)
spec: game-design/decision-2026-09-05-ruling-build-batch-and-roadmap-fold.md, section 11 item D; CLAUDE.md rule 12
acceptance: the publish workflow's pageResult lines land in the tree as a committed file keyed by short sha, so "published" is read from a file rather than from a step summary; a run that measured nothing writes the words "nothing measured" under its own sha and never carries a previous run's file forward under its name
max_sessions: 1
status: READY 2026-09-05. NOT STARTED THIS WEEK by Jafar's rule that after item 4 the studio stops building studio.

## Why this exists at all

CLAUDE.md rule 12 and the CI rules say the evidence channel is A FILE
COMMITTED BY CI. Log tails, step summaries and artifact hosts have all failed
here; a committed file has not.

The publish workflow currently prints `pageResult=OK`, `pageHttp=`,
`pageStampCommit=` and the rest into its own run output. Nothing in the tree
records them. So a session asking "is the glance actually live" has to read a
step summary, which is the channel this project already learned not to trust.

## The specific failure it prevents

A run that measured nothing must SAY SO under its own name. The failure to
guard against is the one this project has hit before: a run carries the
commit, banks nothing, and the previous run's file is read as though it
described the new one. "The build carried the commit" and "the build measured
anything" are different facts.

## Both halves

Accepting: a real publish run writes its file, keyed by short sha, and a
session reads `pageResult=OK` for both pages out of the tree.
Rejecting: a run whose request did not complete writes the words "nothing
measured" with its error under its own sha, and the previous run's file is
still there, unchanged, and is not mistaken for it. Stage by name, never by
directory.
