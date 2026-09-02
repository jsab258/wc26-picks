line: infrastructure (instruments)
spec: production/queue/900-process-audit.md items 8 and 9
acceptance: a doc gate that resolves every D<n> citation against the register and FAILS on one that resolves to nothing, printing both counts; accepting case is the live tree; rejecting case a planted citation to a number no file carries
max_sessions: 1
status: READY 2026-09-02. instrument-builder. The audit items are the manual half; this is the mechanical one.

On 2 September a decision record shipped citing D11, which did not exist,
and DENYING D10, which had existed since commit 0ff1ee17 and is cited from
three documents. Both halves were caught by Jafar rather than by anything in
the tree.

TWO CHECKS, one function, in `tools/docs-check.py`:

1. DANGLING CITATION. Collect every `D<n>` mention across the walked trees,
   map each to `ledger-v2/respec/decision-register/`, and fail on any that
   resolves to no file. Print the citations examined AND the register size,
   because "0 dangling" over a register nobody read is the zero this project
   keeps being fooled by.

2. BARE NUMBER. A citation should be `D10-framework-freeze`, not `D10`. A
   bare number survives a renumbering by silently re-pointing at whatever
   holds that number now, which is indistinguishable from being right.
   Warn rather than fail at first: the tree is full of bare numbers written
   before this rule, and a gate that goes red everywhere on landing teaches
   people to ignore it. Print the count and let a later rung fail it.

The accepting case is the live tree AFTER the D11 backfill. The rejecting
case is a planted citation to a number no file carries, which must name the
citing file and the missing number rather than saying a count went up.

DO NOT let this gate walk `legacy/`. Superseded documents legitimately cite
decisions that were retired, and failing on those would push someone to edit
history to make a gate green.
