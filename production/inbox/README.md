# The inbox: what Jafar sent his bot

STATUS: LIVE. Landed 2026-09-05 by queue 088.

Each file here is one message he typed into the Telegram bot on his phone,
carried to this repository by the PC. The name is
`<YYYY-MM-DD>T<HHMM>Z-<update_id>.md`, dated from Telegram's own clock, and
the file carries the message text, that instant, and the Telegram update id.
It carries no token, no chat id and no path to the credential file, which is
the rule ruled 2026-09-04 and it applies to what goes into git exactly as it
applies to what the bot prints.

## How to read them

    python3 tools/inbox-read.py

That fetches the `pc-inbox` branch, writes anything new into this folder, and
prints it with `inboundLatencySec`. A message that has never arrived prints
the words "nothing measured" beside `delivered=0/0`, so an empty inbox cannot
read like a broken reader. Run it at the start of a turn and at every dispatch
or spawn boundary; the call sites are in `ledger-v2/studio-v2/runner.md` and
in `production/watchdog-prompt.md`.

## Why the files arrive on a branch of their own

`pc-results` is force-pushed from the work branch plus a named list of
produced paths, so anything parked there by another route disappears at the
next PC job. `pc-inbox` has one writer, `tools/runner/inbox.py`, and the bot
never commits inside the watcher's checkout: it writes its commit through a
temporary index, so `tools/pc-watcher.py` cannot be wedged by it. Both
properties are asserted in `python3 tools/runner/inbox.py --selftest`.

## What this half does NOT do

It does not WAKE the studio. A message arrives on the branch about a minute
after he sends it, and it is READ when a session next looks. While the studio
is asleep that is the daily trigger at 04:00 UTC, up to 24 hours away. The
bot's reply says which of the two states it is in and, when asleep, names the
next wake, so the wait is never silent. Closing that gap is queue 092, and
`production/queue/088` carries the measurement that ruled out the route that
looked like the answer.

Delivered files are untracked until the next batch commit stages them by name;
the work branch is the record, `pc-inbox` is the transport. A message sent while
the bot on the PC is NOT running is skipped at the bot's next start, counted in
the PC window and not filed; until the fold in queue 090's pass lands, the bot's
silence is the signal to resend after its opening message.
