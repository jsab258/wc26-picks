line: infrastructure (governance)
spec: game-design/decision-2026-09-02-constitution-cut-attribution-pc-channel.md, Ruling 9
acceptance: the session-start hook prints the head of production/NOW.md's "## In flight" rather than game-design/queue.md's "## Now"; the no-file first-fix branch is kept; a session start shows live state
max_sessions: 1
status: READY 2026-09-02. Small. Rides the next reviewed batch because .claude/ is a work prefix.

`.claude/settings.json` line 32 passes `QUEUE_FILE=game-design/queue.md`, and
`session-start.sh` prints the first item under that file's `## Now`.

That file declared itself SUPERSEDED on 31 August. So every session in this
project has opened by reading the head of a retired queue, for two days, and
the banner text is what it printed.

Point it at `production/NOW.md`'s `## In flight` section instead and print the
first five lines. Keep the "no file, and that is the first thing to fix"
branch: a hook that goes silent when its source is missing is the failure this
whole queue is about.
