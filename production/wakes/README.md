# The wake queue: what is owed at the next turn boundary

STATUS: LIVE. Landed 2026-09-09 for Jafar's ruling of that morning, item 3:
"Wakes. A trigger that fires while the session is mid-turn is lost; it cost him
yesterday's brief. Make wakes queue until the turn ends, and prove it."

Each file here is one durable due record: an id, the instant it comes due, who
armed it and when, how many times a turn boundary has blocked for it, and
whether it has been discharged and when. The name is
`<YYYY-MM-DD>T<HHMM>Z-<id>.wake.txt`, dated from the DUE instant in UTC, so the
directory sorts in the order things come due.

    python3 tools/wake-queue.py arm --due 2026-09-10T04:00:00Z \
        --by director/daily --instruction "Plan the day, write the brief"
    python3 tools/wake-queue.py due          # what is owed right now
    python3 tools/wake-queue.py discharge <id>
    python3 tools/wake-queue.py series       # records per day, blocks per record

## Why this folder exists at all

A trigger reports SUCCEEDED when the wake is DELIVERED, not when the work
happens. Measured on trigger `trig_013itgDeay6t41BHEmaYFbAj`: fired at
2026-09-09T04:09:00.554Z, finished at 04:09:00.567Z, twelve and a half
milliseconds, status SUCCEEDED, no brief written and none sent. The session was
mid-turn and the injected turn was absorbed. The platform's delivery semantics
cannot be changed from inside this repository, so the wake stops being the only
delivery: the record is on disk from the moment it is armed, and
`.claude/hooks/wake-drain.sh`, registered as the Stop hook, reads it at the end
of whatever turn absorbed the wake. Filed as
`production/queue/174-an-armed-trigger-is-half-a-promise.md`.

## Two things about these files

**They are TRACKED, and a discharged record is KEPT.** The container is
ephemeral and reclaimed after inactivity, so a queue in /tmp is a queue that
dies with the machine, which is the failure this folder removes. And the
history is the evidence the mechanism worked: `armedAt`, `due` and
`dischargedAt` in one file is what says a wake was served, where an empty
directory would read exactly like a wake that was never armed.

**Nothing sweeps them, on purpose.** There is no series yet, so no sweep bound
is invented (CLAUDE.md rule 2). `python3 tools/wake-queue.py series` is the
printer: records armed per UTC day, blocks before discharge per record, total
bytes. A bound comes from what it prints over real runs, in that order.

A README is not a record: `tools/wake-queue.py:NAME_RE` matches only
`*.wake.txt` with a dated name, so this file is outside every denominator the
tool prints rather than counted as a record it cannot read.
