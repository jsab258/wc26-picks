line: infrastructure (instruments)
spec: game-design/decision-2026-09-01-cadence-bound-and-batch-review.md, "Queue items"
acceptance: (a) a rule count printed beside the label breakdown, asserted by a17 and a19; (b) one selftest-count parser covering four checks, each with its own accept and reject fixture, and the "0 of N FAILED" string fixed on a non-zero exit; (c) the largest untracked work path named when untracked_files > 0, capped and announced; (d) --cadence-series prints label:lines per commit beside the total
max_sessions: 1
status: READY 2026-09-01, created from the ruling's text. One instrument-builder, one session. Blocks nothing; (d) is the instrument the bound's next rung waits on.

Four follow-ups on `ledger/verify.py`, all named by the director ruling of
1 September after it read the cadence batch. None of them is a fault in what
landed; each is a rung the landed version did not reach.

## (a) pathsEvidence counts LABELS and says RULES

`pathsEvidence` prints "by N of M rule(s)" where N counts distinct labels,
not rules. `propsout` covering two paths is what made the mismatch visible.

Keep `evidence_hits` by label for the printed breakdown, which is the useful
half, and add a rule count beside it. Fixtures a17 and a19 assert the true
numbers. Accepting case: the live tree.

## (b) Four copies of the same selftest-count parse

`ref_bench`, `decal_ink`, the `frame-drift` check at line 2191, and
`_meshgen_suite` each parse "read N passed, M failed" their own way. The
cadence builder named three and added the fourth rather than consolidating;
the director found the missed one at 2191, so the count is FOUR, not three.

Fold them into the shape `_meshgen_suite` has and rename it, since it is no
longer meshgen-specific. Keep the three outcomes. Fix the self-contradicting
"0 of N FAILED" string it prints on a non-zero exit. The fixtures at 5142 to
5153 and 5240 to 5247 are the model; each folded check gets its own accept
and reject.

## (c) Untracked work lines are counted without being named

When `untracked_files > 0` the gate counts those lines into the total and
never says which paths they were. Print the largest untracked work path or
paths, capped and announced when the cap bites.

The `.claude/` observation behind this is narrower than it first looked: it
is true of every prefix, not just that one. For genuinely local files the fix
is a `.gitignore` line for `.claude/*.local.*`, and it goes in ONLY if such a
file ever appears. A gitignore entry for a file that does not exist is a
claim nobody tests.

## (d) The bound's next rung: a per-prefix series

`--cadence-series` prints one total per commit and its `biggest:` line is
`sha:total`, so no instrument in the project can currently see whether the
eight prefixes are one population or several. That is why the ruling set one
bound at 100 and named this as the revisit condition rather than inventing a
per-prefix number.

Print `label:lines` per commit beside the total. Print first. A per-prefix
bound, if there is one, is ruled from what the row shows, never before it.
