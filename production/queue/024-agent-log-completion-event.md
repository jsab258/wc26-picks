line: infrastructure (governance)
spec: game-design/decision-2026-09-02-constitution-cut-attribution-pc-channel.md, Ruling 7
acceptance: step one is a printed payload, not a parser; then a third column accepted at both widths with nothing migrated; then the three consumers in the order below
max_sessions: 3
status: STEP 1 SUBSTITUTED 2026-09-03: the payload was read off the binary rather than printed from a live event, and the hook is now REGISTERED so the first real row is the printed payload 024 asked for. Read it. Then step (d) below. instrument-builder.

THE ATTENDANCE HOLE, THIRD INSTANCE, AND ONE INSTRUMENT FOR ITS THREE
CONSUMERS. `.claude/agent-log.tsv` has two columns, `when` and `agent`. Every
row is a spawn. Nothing marks completion, so no consumer can ask "did that
finish" and three have tried:

- `director_cadence` was satisfied by a spawn rather than a review, and was
  fixed by testing an ARTIFACT (the ruling record) instead of attendance.
- The watchdog's dailies check still tests attendance and was ruled on 25
  August to move to the artifact test.
- Queue 014's preferred fix proposed it a third time and would have gone
  permanently silent.

STEP ONE IS A MEASUREMENT AND IT IS THE WHOLE FIRST SESSION. Claude Code
fires a `SubagentStop` event and NOBODY IN THIS PROJECT HAS PRINTED WHAT ITS
PAYLOAD CARRIES. Write a hook that appends the raw payload KEYS to a scratch
file for one session, then report them. Building a parser on an unread
payload is the exact fault this project's rule set is about.

STEP TWO, only after step one lands. The log gains a third column `event`
with values `start` and `stop`. Every existing two-column row reads as
`start` BY CONSTRUCTION, so the parser accepts both widths and NOTHING IS
MIGRATED.

STEP THREE, the three consumers, in this order:
(a) L32's resume inflation: a `stop` row lets a resume be told from a fresh
    spawn, so the footer's `directorSpawns` stops over-counting.
(b) The watchdog dailies test, moving to the artifact test as ruled 25 Aug.
(c) The stop hook: a `start` with no matching `stop` for the same agent type
    means a builder is running, and the hook PRINTS WHY IT IS QUIET, which is
    queue 014's closing demand.

STEP THREE (d), added 2026-09-03: the coverage pair. `spawn-cost --report`
prints rows-with-a-turn-record over rows in agent-log.tsv; 454 transcripts on
the machine against 240 logged rows is unexplained, and 149 of the 454 never
produced a turn.

RESOLVED BY THE COMMITTED SERIES, 2026-09-03, and recorded here so the next
reader does not re-open it: the 148 and the 149 are two different facts, not a
typo for each other. `production/spawn-cost-series-2026-09-03.txt` prints
`170 of 454 spawn(s) carry a session-limit notice, and 148 of those 170
produced NO turn at all` beside `no-model spawns=149`. So 148 is dead AND
noticed, 149 is dead in total, and 22 spawns hit the wall after doing work.
The 214-row gap between transcripts and logged rows is what is still open.

Then the per-tier POINTS figure: two paired readings from Jafar, both meters,
with the turns log between them. Until that prints, budget.md carries turns
and not points per tier, and queue 076 carries the tokens-per-point rate that
would replace the guess outright.
