line: infrastructure (instruments)
spec: this file
acceptance: propview --selftest runs inside ledger/verify.py with its count in the footer; the same pass covers meshgen --selftest, which is also unwired
max_sessions: 1
done: 2026-09-01 by director ruling game-design/decision-2026-09-01-cadence-bound-and-batch-review.md, Ruling 1 item 7. Acceptance met: both selftests run inside ledger/verify.py with their counts in the footer (check list at line 5574), and every widening the item carried is in the constants.
status: READY 2026-09-01. Unblocked by the cadence ruling and WIDENED by it: this
        is now the single next touch of ledger/verify.py and carries every code
        consequence of that ruling, one builder spawn rather than three.

`tools/meshgen/propview.py --selftest` passes 59 checks and nothing runs it.
`tools/meshgen/meshgen.py --selftest` passes 102 and nothing runs those either.

The builder named this itself rather than leaving it to be found, and it is
the project's own standing rule: an unwired test decays, because a test
nobody runs is already wrong and does not know it. Both wire the same way,
one function each beside the existing lint calls.

Do both in one pass. Wiring one and leaving the other is how a rule becomes
a habit of doing half of it.

WIDENED 2026-09-01 by game-design/decision-2026-09-01-cadence-widening-and-propview-batch.md.
Read the ruling's section naming the scope function by function. In addition to
wiring the two selftests, this task carries:

- content/props/manifest.json and content/props/ATTRIBUTION.json become EVIDENCE
  by exact path. They are machine-written about a run and published by meshgen's
  own commit with no verify in the path, which is the same class as mesh reports
  and CI stills. content/ itself stays WORK: the dialogue bank and brand bible
  are authored.
- .claude/ comes IN as work (hooks, settings, agent definitions, which carry the
  model line the gate itself reads), with .claude/template-sync.txt joining the
  agent log as evidence.
- Plans, specs and ledger-v2/ stay OUT of the line gate. They reach the director
  by trigger kind rather than by volume, and a prose bound was never measured.

DO NOT set the bound in this task. The ruling declined to set it because the
series was measured under a classifier this very task changes, and its three
largest readings are the manifest files now becoming evidence. After this lands,
print `--cadence-series 120` and paste the raw sorted line into the next
mandatory director brief; the bound is ruled there, from the row rather than
from a summary.
