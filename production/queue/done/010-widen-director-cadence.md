line: infrastructure (governance)
spec: this file, plus learning.md L26 and L27
acceptance: director_cadence counts work across a named prefix set with an evidence-exclusion list; the printed line names what was walked and what was excluded; the selftest gains a fixture reproducing 2026-09-01 (substantial work entirely outside Assets/Scripts, no director row) that MUST go red and would have gone green before
max_sessions: 2
status: DONE 2026-09-01, landed by director ruling
        game-design/decision-2026-09-01-cadence-widening-and-propview-batch.md.
        The gate now counts a named work set minus a named evidence list, prints
        the per-prefix breakdown with its denominators, and says out loud that the
        100-line bound is INHERITED and not yet evidence-based. Selftest 55 to 75,
        including a fixture reproducing 1 September that goes RED under the new
        scope and GREEN under the old, restored in a finally and asserted.
        Measured on landing: 20,618 work lines across 89 commits dated 2026-09-01
        under the new scope, 0 under the old, and the old reference instant was
        6.7 days stale.

director_cadence measures substantial work ONLY as changed lines under
ledger/Assets/Scripts (constant DIRECTOR_SCRIPTS in ledger/verify.py). On
2026-09-01 the session did a full day of substantive work with zero director
review and zero agent spawns, and the gate printed "0 changed line(s) vs 100
threshold under Assets/Scripts, under threshold, review not required" all day.

It did not fail. It is blind to where this project's work now happens. The
v2 respec moved the centre of gravity out of the Unity tree in a single day
and nobody re-asked what the gate was watching.

Reviewed scope should become a named set, at minimum: ledger/Assets/Scripts/,
ledger/ python, tools/, .github/workflows/, .githooks/, ue-probe/, content/.
Excluded as EVIDENCE rather than work, each with its reason written down:
game-design/sim-shots/, the production/d1-probe/ outputs, production/briefs/,
.claude/agent-log.tsv, ledger/.verify-footer.

DO NOT REGRESS THE EXISTING FIX. The reference commit must stay "the last
commit that TOUCHED the reviewed scope", never HEAD; that cost three false
reds to get right and its docstring says so.

DO NOT INVENT A THRESHOLD. 100 was set against Assets/Scripts alone. Ship the
printer first, read a real series, then set a bound. If a bound is needed to
stay useful today, keep 100 and say in the output that it is inherited from a
narrower scope and is not yet evidence-based.
