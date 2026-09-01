line: instrument (D1 probe, measurement a)
spec: production/d1-probe/plan.md, measurement a
acceptance: cycles.tsv holds at least 20 Unity rows written AS THE EDITS HAPPEN; median and failed-edit rate computed from the file, never from memory
max_sessions: 2

Build production/d1-probe/cycles.tsv and start filling the Unity half.

One row per real edit, written at the time: engine, task-id, edit start
(ISO), test result seen (ISO), outcome (pass, fail, or failed-edit), and
what was edited. A failed-edit means the edit could not be applied or was
lost, which is the binary-asset failure mode UE is being measured for; in
Unity it should be near zero and that zero is the comparison's floor.

Rows come from work that was happening anyway. Do NOT manufacture edits to
fill the file; a synthetic cycle time measures the harness, not the loop.

Print median and failed-edit rate with their denominator (rows counted).
D1's measurement a is a MEDIAN over real edits, not a mean and not a
best-case: name it in the file header so the next reader cannot mistake it.
