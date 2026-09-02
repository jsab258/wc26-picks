line: infrastructure (governance)
spec: game-design/decision-2026-09-02-constitution-cut-attribution-pc-channel.md, Ruling 7
acceptance: step one is a printed payload, not a parser; then a third column accepted at both widths with nothing migrated; then the three consumers in the order below
max_sessions: 3
status: READY 2026-09-02. One instrument-builder. RESEARCH FIRST, and step one is the whole first session.

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
