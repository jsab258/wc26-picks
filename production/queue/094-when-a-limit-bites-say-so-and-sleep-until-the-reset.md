line: infrastructure (limit visibility)
spec: production/NOW.md, "JAFAR'S STANDING ORDER, 2026-09-05", items 1b and 1e
acceptance: given the one real notice this repo holds, the parser writes a state file reading limitKind=session and resetAtUtc as an ISO instant naming the file it was parsed from, and the bot says "studio paused, back at HH:MM" in a named time zone and says so again when it resumes; the night runner given a state file whose reset is three minutes ahead SLEEPS and then spawns exactly once, proven by the log timestamps either side; a log with no notice writes NO state file and prints the words "nothing measured" with logsScanned=N; a notice whose time cannot be parsed writes resetAtUtc=unknown, makes the bot say paused with NO time and raise a CLASS: BLOCKING card, and never substitutes a default; a state file whose reset is already past is named expired and does not make the runner sleep; with the newest work-branch commit older than two hours and no state file, the bot raises a CLASS: BLOCKING card, and with a state file whose reset is ahead it does not, both proven with planted clocks, printing silenceHours beside the two-hour bound and the two instants compared; resumed means the state file cleared by the container's first turn after the reset, with the newest commit instant as the fallback signal, and the bot's back-again line names which; a reset beyond the runner's own wall-clock deadline ends the night with that reason in the log rather than sleeping past it
max_sessions: 1
status: READY 2026-09-05. After item 1 and before the trial night. instrument-builder. Item 1e runs BY HAND until this lands.

## The evidence base, with its denominator, because it is small

ONE real notice string exists in this tree, quoted in `production/budget.md`
from a 429 received on 2026-09-02: "You've hit your session limit, resets
12:20am (UTC)". That is the accepting fixture and it is a denominator of 1.

A larger corpus exists and is NOT in the container: the same file records 170
of 454 transcripts on the build machine carrying a session-limit notice, 148 of
those 170 having produced no turn at all. The builder is on that machine, so
the parser gets tested against real strings there, and the acceptance prints
`noticesParsed=N/M` over what it actually read. If the transcripts cannot be
reached, the file says so and the denominator stays 1 rather than being
implied to be larger.

## The distinction that must survive into the file

There are TWO limits and budget.md's own history is a record of them being
confused. The 5-hour session limit resets many times a week and says nothing
about the weekly meter; the weekly limit was Monday 14:00 CEST until it reset
early on 2026-09-05, which is itself a regime change. So the state file carries
`limitKind` and no reader may infer one from the other. A notice that does not
say which limit it is writes `limitKind=unknown`, not a guess.

Shape, key=value with no spaces inside values, per the instrument rules:

    state=paused limitKind=session resetAtUtc=2026-09-03T00:20Z
    noticeSeenAtUtc=... parsedFrom=<path>

The bot's line to him converts to a named zone. "back at 12:20" with no zone is
the same ambiguity that put an hour into the 2 September timeline.

## The runner burns iterations into a closed session today

`tools/runner/run-night.ps1` runs `claude -p $dispatch --max-turns 200`, then
on a non-zero exit writes one line and goes straight round the loop. Against a
session limit that is 40 iterations of nothing, spending wall clock and
producing logs that all say the same thing. It must read the state file, sleep
until the reset, and never sleep past its own wall-clock deadline: a reset
beyond the deadline ends the night with that reason named.

## Silence is a state and it needs an owner

A studio silent more than two hours with no reset time on file is a CLASS:
BLOCKING item per `production/interrupt-classes.md`. The detector cannot live
in the container, because the container being asleep is the case it exists for.
It lives with the bot, reads the newest commit instant on the work branch
against the state file, and pushes the card.

## Until this lands, item 1e is armed by hand

When a limit is hit, arm a one-shot trigger for the parsed reset whose
instruction is to resume the current item and continue the standing order. Rule
8 binds: arming happens in the same turn as the promise, and a remembered
intention is not a watcher. NO RESET MAY EVER NEED JAFAR TO RESTART THE STUDIO.

## If it does not fit in one session

Land the parser, the state file and the runner sleep first, write the resumable
state under `production/scratch/`, and enqueue a continuation NUMBERED BY THE
DIRECTOR. Do not pick a queue number in a builder pass; two collisions in two
days are why that rule exists.

## Depends on, and what it blocks

Depends on queue 088 only for the bot half to reach the repo; the parser and
the runner sleep depend on nothing. Blocks queue 103, the supervised trial
night, which is not worth running while a limit silently burns iterations.
