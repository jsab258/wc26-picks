line: infrastructure (the evidence channel)
spec: game-design/decision-2026-09-05-ruling-build-batch-and-roadmap-fold.md, section 4 and section 11 item B
acceptance: the gate refuses a commit while an untracked record sits in production/inbox, production/outbound OR production/rulings, printing inboxUntracked=N/M per directory with the words "nothing measured" on an empty one; a rejecting fixture PER DIRECTORY, accepting case first
max_sessions: 1
status: READY 2026-09-05. NOT STARTED THIS WEEK by Jafar's rule that after item 4 the studio stops building studio.

## The gap

The gate landed on 2026-09-05 watches `production/inbox/` only. Three
directories now carry records that arrive from the PC and are untracked until
something stages them:

- `production/inbox/` messages Jafar sends. WATCHED.
- `production/outbound/` receipts and refusal records from the sender. NOT
  WATCHED.
- `production/rulings/` the records a tapped button writes. NOT WATCHED, and
  it does not exist yet: it is created by the first tap on his PC.

So two of the three can accumulate silently and be lost when the branch is
force-pushed, which is exactly the loss the first gate exists to prevent.

## Why a fixture per directory rather than one

A single fixture over a glob passes when the glob is wrong. Three directories
means three ways for the walk to miss one, and a gate that watches two of
three while printing one number is the false-clean this project has a rule
about. Each directory gets its own planted record and its own refusal.

## Both halves

Accepting: all three empty, the gate green, printing the words "nothing
measured" against a real count of what it walked.
Rejecting: a planted untracked record in EACH directory in turn refuses the
commit and names which directory and which file.
