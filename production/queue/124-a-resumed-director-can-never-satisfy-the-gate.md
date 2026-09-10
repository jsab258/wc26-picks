line: studio (the gate that blocks commits)
spec: this file. Filed 2026-09-06 and REFUTED the same day.
acceptance: none. There is nothing here to build.
max_sessions: 0
status: CLOSED 2026-09-10, not on the ladder; filed as a finding rather than as ladder work 2026-09-06, by the director spawned to rule the register batch,
  and confirmed by the resident against the code and against a run that was
  already in hand. KEPT, not deleted, because the way it was wrong is the
  useful part.

## What this item claimed

That a killed and resumed director can never satisfy `director_cadence` on its
first pass, by construction, because the resume logs a new director row and the
gate demands a ruling naming the newest row.

## Why that is false

`ledger/verify.py` at 3444 to 3455: the cadence state becomes `unruled` only
when `ruling_fresh == 0`. ONE stamp naming ANY fresh row clears it. The gate
never demanded the newest row.

`rulingUnruledNewest` is not what the gate reads. Its own docstring at 3655 to
3661 says so in as many words: it prints on GREEN lines too, and it is named
for what it IS rather than for what the red branch wants.

Fixture a14 at 4346 to 4363 is the ACCEPTING CASE for exactly this scenario:
two fresh director spawns, one ruling, GREEN, with `rulingRowsUnruled=1/2`
printed as an unbounded reading. The situation this item called impossible is
the situation the guard was written to pass, and somebody had already tested
it.

## How the resident got it wrong, which is the part worth keeping

The evidence was in hand and was misread. Two runs:

- Run 1, before any ruling existed: `DIRECTOR RAN BUT DID NOT RULE ...
  rulingRowsUnruled=1/1`. Red, and correctly so.
- Run 2, after the ruling landed: the same footer reads `director cadence ok
  (2649 changed line(s) ... vs 100 threshold over the reviewed scope`, and
  separately `UNTRACKED/ABSENT TOOL(S): StrangerTest`.

The resident read `rulingRowsUnruled=1/2` out of run 2, recognised it as the
same key that had been red in run 1, and concluded the cadence gate was still
failing. The words `director cadence ok` were in the same footer, feet away.
The gate had gone green the moment the ruling landed, exactly as designed, and
the red was a different check entirely: an untracked tool.

CLAUDE.md rule 2, second sentence: the same evidence is owed for WHICH number a
gate reads as for the number itself. A key that was red in one run is not the
key that is red in the next, and the only way to know is to read the verdict
the gate prints rather than the reading beside it. An unbounded reading that
moves looks exactly like a bound that is failing, and this is what that costs:
a queue item, a wrong instruction to a director, and two round trips.

## What survives, and it is small

One sentence, and it is documentary rather than a defect. A ruling cannot name
a row that does not exist yet, so a director stamps what it can attribute and
says so. The director's record does this: it carries the two rows it can
attribute and names a third, `2026-09-06T09:13:12Z`, as probable but
unattributable, because `.claude/agent-log.tsv` has two columns, `when` and
`agent`, and no agent identity. That absence is real and is recorded here for
whoever next wants to collapse a resume chain. It is not blocking anything and
it is not worth a build on its own.
