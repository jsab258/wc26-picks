line: infrastructure (the roadmap)
spec: game-design/decision-2026-09-05-ruling-build-batch-and-roadmap-fold.md, section 11 item C
acceptance: a checker prints, per roadmap row, the word count against the 80 cap, whether an instrument link is present, whether a verified date is present, and the systems column against the tool's own per-phase census; red on any row over the cap, missing either field, or whose column disagrees with production/systems-inventory.json; both outcomes with the accepting case first, the accepting fixture being the live roadmap
max_sessions: 1
status: READY 2026-09-05. NOT STARTED THIS WEEK by Jafar's rule that after item 4 the studio stops building studio.

## The row law nothing enforces

`ledger-v2/respec/roadmap-v2.md` opens by stating its own law: "each milestone
row stays under 80 words, carries an instrument link and a verified date;
detail lives in a milestone file; landed rows move to roadmap-history. Rows
over the cap, or stale against code changes touching their area, fail the
doc-decay gate."

MEASURED 2026-09-05: 0 of 8 rows carries the instrument link or the verified
date the law demands, and NO TOOL CHECKS ANY OF IT. `tools/docs-check.py`'s
root is `game-design/` only and it prints `ledger-v2/` in its NOT WALKED line.
A repo-wide grep for `doc-decay` returns three markdown files and no tool. So
the doc-decay gate the row law names does not exist.

That is a law written for a reader and enforced by nobody, in the file the
whole plan hangs on.

## The systems column is the new half

The fold of 2026-09-05 added a column carrying a per-phase count with its
denominator. It was hand-censused and matched the tool exactly today:
`R=0/27 0=1/27 1=3/27 2=7/27 3=4/27 4=2/27 5=1/27 6=9/27`. A hand census is
right once; it decays the moment a system moves phase. The checker reads the
column and the tool and refuses when they disagree.

## The trap in the word count

The 80-word cap is per ROW, not per file, and the table's pipes and the column
headers are not row words. Say what the counter counts before setting it
loose, and print the worst row's count beside the cap so the number is
readable rather than merely green. Worst row today is 70 of 80.
